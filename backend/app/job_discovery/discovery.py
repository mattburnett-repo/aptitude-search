"""Stage 3 discovery: profile-driven queries + search_job_postings."""

from __future__ import annotations

import logging
import re

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import (
    FoundJob,
    JsonObject,
    OccupationMatchJson,
    as_object_dict,
    as_object_list,
)
from app.core.models import Constraints
from app.core.profile_text import profile_labels, string_list
from app.core.progress import ProgressCallback, emit_progress
from app.job_discovery.tools import search_job_postings

logger = logging.getLogger(__name__)

# Match frontend OccupationMatchesDisplay medium+ band (high ≥ 0.70, medium ≥ 0.65).
_ONET_PREFERRED_MIN_SCORE = 0.65

# Only used for skill-fallback queries (core/secondary skills). Role-family /
# adjacent_roles / domains / interests queries ignore this — those terms are
# already role- or subject-shaped.
_SENIORITY_MODIFIER = {
    "entry": "junior",
    "mid": "",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "executive": "director",
}

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
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)


def _normalize_search_term(label: str) -> str:
    """Compact a profile label into a web-search phrase."""
    stripped = " ".join(label.replace("/", " ").split())
    if "(" not in stripped:
        return stripped
    main, _, rest = stripped.partition("(")
    main = main.strip()
    rest = rest.rstrip(")").strip()
    if rest:
        return f"{main} {rest}".strip()
    return main


def _seniority_modifier(seniority_band: str) -> str:
    return _SENIORITY_MODIFIER.get(seniority_band, "")


def _location_tokens(constraints: Constraints) -> list[str]:
    tokens: list[str] = []
    location = constraints.location.strip()
    if location:
        tokens.append(location)
    if constraints.remote_preference == "remote":
        tokens.append("remote")
    elif constraints.remote_preference == "hybrid":
        tokens.append("hybrid")
    elif constraints.remote_preference == "onsite":
        tokens.append("onsite")
    return tokens


def _significant_tokens(phrase: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", phrase.lower())
    return {token for token in tokens if len(token) >= 4 and token not in _STOP_WORDS}


def _token_overlap(left: str, right: str) -> int:
    left_tokens = _significant_tokens(left)
    right_tokens = _significant_tokens(right)
    if not left_tokens or not right_tokens:
        return 0
    return len(left_tokens & right_tokens)


def _preferred_and_low_onet_titles(
    occupation_matches: list[OccupationMatchJson] | None,
) -> tuple[list[str], list[str]]:
    if not occupation_matches:
        return [], []
    preferred: list[str] = []
    low: list[str] = []
    for raw in occupation_matches:
        row = as_object_dict(raw)
        if row is None:
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        try:
            score = float(row.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        if score >= _ONET_PREFERRED_MIN_SCORE:
            preferred.append(title)
        else:
            low.append(title)
    return preferred, low


def _family_onet_sort_key(
    family_label: str,
    terms: list[str],
    *,
    preferred_titles: list[str],
    low_titles: list[str],
) -> tuple[int, int, int]:
    """Higher key = pick this family's terms earlier (prefer high/medium O*NET)."""
    phrases = [family_label, *terms]
    preferred_hits = sum(
        1
        for title in preferred_titles
        if any(_titles_relate(phrase, title) for phrase in phrases)
    )
    low_hits = sum(
        1
        for title in low_titles
        if any(_titles_relate(phrase, title) for phrase in phrases)
    )
    # Prefer families that align with preferred O*NET titles; demote low-only.
    return (1 if preferred_hits > 0 else 0, preferred_hits, -low_hits)


def _titles_relate(left: str, right: str) -> bool:
    """True when two occupation/title phrases share a meaningful stem overlap."""
    if _token_overlap(left, right) >= 2:
        return True
    left_l = left.lower()
    right_l = right.lower()
    if left_l in right_l or right_l in left_l:
        return True
    left_stems = {token.rstrip("s") for token in _significant_tokens(left)}
    right_stems = {token.rstrip("s") for token in _significant_tokens(right)}
    shared = left_stems & right_stems
    return any(len(stem) >= 5 for stem in shared)


def _term_is_low_only(
    term: str,
    *,
    preferred_titles: list[str],
    low_titles: list[str],
) -> bool:
    """True when a search term aligns with low O*NET titles but not preferred ones."""
    if not low_titles:
        return False
    if any(_titles_relate(term, title) for title in preferred_titles):
        return False
    return any(_titles_relate(term, title) for title in low_titles)


def _discovery_search_terms_from_plan(
    role_family_plan: JsonObject,
    *,
    max_queries: int,
    occupation_matches: list[OccupationMatchJson] | None = None,
) -> list[tuple[str, str]]:
    """Pick search terms, preferring families aligned with high/medium O*NET matches."""
    families_raw = as_object_list(role_family_plan.get("recommended_role_families"))
    if families_raw is None:
        return []

    preferred_titles, low_titles = _preferred_and_low_onet_titles(occupation_matches)

    family_rows: list[tuple[tuple[int, int, int], str, list[str]]] = []
    for family in families_raw:
        family_dict = as_object_dict(family)
        if family_dict is None:
            continue
        label = str(family_dict.get("role_family") or "").strip()
        terms = string_list(family_dict.get("search_terms"), limit=max_queries)
        if not terms:
            continue
        key = _family_onet_sort_key(
            label,
            terms,
            preferred_titles=preferred_titles,
            low_titles=low_titles,
        )
        family_rows.append((key, label, terms))

    family_rows.sort(key=lambda row: row[0], reverse=True)
    if not family_rows:
        return []

    preferred_families = [terms for key, _, terms in family_rows if key[0] == 1]
    deferred_families = [terms for key, _, terms in family_rows if key[0] == 0]
    # When O*NET preferred titles exist, exhaust aligned families before low-only ones.
    ordered_groups = (
        [preferred_families, deferred_families]
        if preferred_titles and preferred_families
        else [[terms for _, _, terms in family_rows]]
    )

    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    skipped_low_only: list[str] = []

    for per_family in ordered_groups:
        if not per_family or len(selected) >= max_queries:
            continue
        index = 0
        while len(selected) < max_queries:
            added = False
            for terms in per_family:
                if index >= len(terms):
                    continue
                label = terms[index]
                added = True
                if label in seen:
                    continue
                if preferred_titles and _term_is_low_only(
                    label,
                    preferred_titles=preferred_titles,
                    low_titles=low_titles,
                ):
                    skipped_low_only.append(label)
                    continue
                seen.add(label)
                selected.append(("role_family", label))
                if len(selected) >= max_queries:
                    break
            if not added:
                break
            index += 1

    if len(selected) < max_queries and skipped_low_only:
        for label in skipped_low_only:
            if label in seen:
                continue
            seen.add(label)
            selected.append(("role_family", label))
            if len(selected) >= max_queries:
                break

    if skipped_low_only:
        logger.info(
            "discovery deferred low-O*NET search_terms=%s kept=%s",
            skipped_low_only,
            [term for _, term in selected],
        )
    return selected


def _discovery_search_terms(
    aptitude_profile: JsonObject,
    *,
    max_queries: int,
    role_family_plan: JsonObject | None = None,
    occupation_matches: list[OccupationMatchJson] | None = None,
) -> list[tuple[str, str]]:
    """Return (source, term) pairs for discovery queries."""
    if role_family_plan is not None:
        plan_terms = _discovery_search_terms_from_plan(
            role_family_plan,
            max_queries=max_queries,
            occupation_matches=occupation_matches,
        )
        if plan_terms:
            return plan_terms

    terms: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(source: str, label: str) -> None:
        if label in seen or len(terms) >= max_queries:
            return
        seen.add(label)
        terms.append((source, label))

    for label in profile_labels(aptitude_profile.get("adjacent_roles"), limit=max_queries):
        add("adjacent_roles", label)

    if len(terms) < max_queries:
        for label in profile_labels(
            aptitude_profile.get("domains"),
            limit=max_queries - len(terms),
        ):
            add("domains", label)

    if len(terms) < max_queries:
        for label in profile_labels(
            aptitude_profile.get("interests"),
            limit=max_queries - len(terms),
        ):
            add("interests", label)

    if not terms:
        for label in profile_labels(
            aptitude_profile.get("core_skills"),
            limit=max_queries,
        ):
            add("core_skills", label)
        if len(terms) < max_queries:
            for label in profile_labels(
                aptitude_profile.get("secondary_skills"),
                limit=max_queries - len(terms),
            ):
                add("secondary_skills", label)

    return terms


def _query_parts(
    source: str,
    term: str,
    *,
    seniority_modifier: str,
    loc_tokens: list[str],
) -> list[str]:
    """Assemble a hiring-shaped query without hardcoding an occupational family."""
    normalized = _normalize_search_term(term)
    if source in {"role_family", "adjacent_roles", "domains", "interests"}:
        return [normalized, *loc_tokens, "jobs"]
    if seniority_modifier:
        return [seniority_modifier, normalized, *loc_tokens, "jobs"]
    return [normalized, *loc_tokens, "jobs"]


def build_discovery_queries(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    *,
    role_family_plan: JsonObject | None = None,
    occupation_matches: list[OccupationMatchJson] | None = None,
    max_queries: int | None = None,
) -> list[str]:
    """Build hiring-shaped search strings from role families, profile, and constraints."""
    if max_queries is None:
        max_queries = config.job_discovery.discovery_query_max

    seniority = str(aptitude_profile.get("seniority_band") or "unknown")
    modifier = _seniority_modifier(seniority)
    loc_tokens = _location_tokens(constraints)

    queries: list[str] = []
    for source, term in _discovery_search_terms(
        aptitude_profile,
        max_queries=max_queries,
        role_family_plan=role_family_plan,
        occupation_matches=occupation_matches,
    ):
        queries.append(
            " ".join(
                _query_parts(
                    source,
                    term,
                    seniority_modifier=modifier,
                    loc_tokens=loc_tokens,
                )
            )
        )
    return queries


def _merge_jobs(
    found_jobs: list[FoundJob],
    seen_urls: set[str],
    new_jobs: list[FoundJob],
) -> int:
    added = 0
    for job in new_jobs:
        url = str(job.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        found_jobs.append(job)
        added += 1
    return added


@traceable(run_type="chain", name="job_discovery")
def run_job_discovery(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    *,
    role_family_plan: JsonObject | None = None,
    occupation_matches: list[OccupationMatchJson] | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[FoundJob]:
    """Stage 3 discovery: web search for open postings (no LLM).

    - Build hiring-shaped queries from role family ``search_terms`` when
      present (else profile adjacent_roles / domains / interests / skills).
    - Prefer terms aligned with high/medium O*NET matches when provided.
    - Run ``search_job_postings`` for each query (this is the actual web search).
    - Return URL-deduped ``found_jobs`` for aptitude-fit ranking and synthesis.
    """
    queries = build_discovery_queries(
        aptitude_profile,
        constraints,
        role_family_plan=role_family_plan,
        occupation_matches=occupation_matches,
    )
    if not queries:
        logger.warning("job_discovery built zero queries from profile")
        return []

    found_jobs: list[FoundJob] = []
    seen_urls: set[str] = set()
    total = len(queries)

    for index, query in enumerate(queries, start=1):
        emit_progress(
            f"Searching the web ({index}/{total}): {query}…",
            on_progress=on_progress,
        )
        # Web search for this query; append new URLs only (dedupe via seen_urls).
        added = _merge_jobs(found_jobs, seen_urls, search_job_postings(query))
        logger.info(
            "job_discovery query=%r jobs_added=%s total=%s",
            query,
            added,
            len(found_jobs),
        )

    logger.info("job_discovery found_jobs count=%s", len(found_jobs))
    return found_jobs
