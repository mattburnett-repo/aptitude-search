"""Rank and filter found_jobs by aptitude work-pattern fit."""

from __future__ import annotations

import logging
import re

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.core.profile_text import profile_labels, string_list

logger = logging.getLogger(__name__)

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "over",
        "under",
        "this",
        "that",
        "than",
        "via",
        "who",
        "high",
        "low",
        "only",
        "listed",
        "skills",
        "section",
    }
)


def _significant_tokens(phrase: str) -> list[str]:
    tokens: list[str] = re.findall(r"[a-z0-9]+", phrase.lower())
    return [token for token in tokens if len(token) >= 4 and token not in _STOP_WORDS]


def _phrase_hits(text: str, phrase: str) -> bool:
    lowered = phrase.lower()
    if lowered in text:
        return True
    tokens = _significant_tokens(phrase)
    if not tokens:
        return False
    hits = sum(1 for token in tokens if token in text)
    return hits >= min(2, len(tokens))


def _family_string_list(
    role_family_plan: JsonObject | None,
    key: str,
    *,
    lowercase: bool = False,
) -> list[str]:
    """Collect string list fields from each recommended_role_families entry."""
    if role_family_plan is None:
        return []
    families = as_object_list(role_family_plan.get("recommended_role_families"))
    if families is None:
        return []
    values: list[str] = []
    for family in families:
        family_dict = as_object_dict(family)
        if family_dict is None:
            continue
        values.extend(string_list(family_dict.get(key), lowercase=lowercase))
    return values


def _job_text(job: FoundJob) -> str:
    parts = [
        str(job.get("title") or job.get("role") or ""),
        str(job.get("company") or ""),
        str(job.get("location") or ""),
        str(job.get("snippet") or job.get("content") or ""),
    ]
    return " ".join(parts).lower()


def score_job_aptitude_fit(
    job: FoundJob,
    aptitude_profile: JsonObject,
    *,
    role_family_plan: JsonObject | None = None,
) -> tuple[int, list[str]]:
    """Score a posting against work patterns; negative score means hard reject."""
    text = _job_text(job)
    if not text.strip():
        return (-999, ["empty_job_text"])

    for avoid in _family_string_list(role_family_plan, "avoid_terms", lowercase=True):
        if avoid and avoid in text:
            return (-999, [f"avoid:{avoid}"])

    score = 0
    signals: list[str] = []

    for label in profile_labels(aptitude_profile.get("strengths")):
        if _phrase_hits(text, label):
            score += 3
            signals.append(f"strength:{label}")

    for label in profile_labels(aptitude_profile.get("working_style_signals")):
        if _phrase_hits(text, label):
            score += 3
            signals.append(f"working_style:{label}")

    for label in profile_labels(aptitude_profile.get("adjacent_roles")):
        if _phrase_hits(text, label):
            score += 4
            signals.append(f"adjacent_role:{label}")

    search_terms = _family_string_list(
        role_family_plan, "search_terms", lowercase=True
    )
    for term in search_terms:
        if term in text:
            score += 2
            signals.append(f"role_family_search:{term}")

    for mode in _family_string_list(role_family_plan, "work_modes"):
        if _phrase_hits(text, mode):
            score += 2
            signals.append(f"work_mode:{mode}")

    if (
        score == 0
        and search_terms
        and not any(term in text or _phrase_hits(text, term) for term in search_terms)
    ):
        # Hard-reject: role family plan had search terms but none aligned.
        return (-1, ["penalty:no_role_family_alignment"])

    return score, signals


def rank_and_filter_found_jobs(
    jobs: list[FoundJob],
    aptitude_profile: JsonObject,
    *,
    role_family_plan: JsonObject | None = None,
) -> list[FoundJob]:
    """Drop avoid-term rows, rank by aptitude fit, return top_k."""
    if not jobs:
        return []

    top_k = config.job_discovery.result_top_k

    scored: list[tuple[FoundJob, int, list[str]]] = []
    for job in jobs:
        fit_score, fit_signals = score_job_aptitude_fit(
            job,
            aptitude_profile,
            role_family_plan=role_family_plan,
        )
        if fit_score < 0:
            logger.info(
                "aptitude_fit rejected url=%r signals=%s",
                job.get("url"),
                fit_signals,
            )
            continue
        scored.append((job, fit_score, fit_signals))

    scored.sort(key=lambda row: row[1], reverse=True)
    selected = scored[:top_k]

    ranked: list[FoundJob] = []
    for job, fit_score, fit_signals in selected:
        enriched = dict(job)
        enriched["aptitude_fit_score"] = fit_score
        enriched["aptitude_fit_signals"] = fit_signals
        ranked.append(enriched)

    removed = len(jobs) - len(ranked)
    if removed:
        logger.info(
            "aptitude_fit removed %s row(s); kept %s ranked by work-pattern fit",
            removed,
            len(ranked),
        )
    return ranked
