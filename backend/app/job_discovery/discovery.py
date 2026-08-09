"""Stage 3 discovery: profile-driven queries + search_job_postings."""

from __future__ import annotations

import logging

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.core.models import Constraints
from app.core.profile_text import profile_labels
from app.core.progress import ProgressCallback, emit_progress
from app.job_discovery.tools import search_job_postings

logger = logging.getLogger(__name__)

# Seniority modifiers only — never assume an occupational family (e.g. "software engineer").
_SENIORITY_MODIFIER = {
    "entry": "junior",
    "mid": "",
    "senior": "senior",
    "staff": "staff",
    "principal": "principal",
    "executive": "director",
}


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


def _discovery_search_terms_from_plan(
    role_family_plan: JsonObject,
    *,
    max_queries: int,
) -> list[tuple[str, str]]:
    """Round-robin search_terms across role families."""
    families_raw = as_object_list(role_family_plan.get("recommended_role_families"))
    if families_raw is None:
        return []

    per_family: list[list[str]] = []
    for family in families_raw:
        family_dict = as_object_dict(family)
        if family_dict is None:
            continue
        terms = profile_labels(family_dict.get("search_terms"), limit=max_queries)
        if terms:
            per_family.append(terms)

    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    if not per_family:
        return selected

    index = 0
    while len(selected) < max_queries:
        added = False
        for terms in per_family:
            if index >= len(terms):
                continue
            label = terms[index]
            if label not in seen:
                seen.add(label)
                selected.append(("role_family", label))
                if len(selected) >= max_queries:
                    break
            added = True
        if not added:
            break
        index += 1
    return selected


def _discovery_search_terms(
    aptitude_profile: JsonObject,
    *,
    max_queries: int,
    role_family_plan: JsonObject | None = None,
) -> list[tuple[str, str]]:
    """Return (source, term) pairs for discovery queries."""
    if role_family_plan is not None:
        plan_terms = _discovery_search_terms_from_plan(
            role_family_plan,
            max_queries=max_queries,
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
    if source in {"role_family", "adjacent_roles", "domains"}:
        return [normalized, *loc_tokens, "jobs"]
    if seniority_modifier:
        return [seniority_modifier, normalized, *loc_tokens, "jobs"]
    return [normalized, *loc_tokens, "jobs"]


def build_discovery_queries(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    *,
    role_family_plan: JsonObject | None = None,
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
    on_progress: ProgressCallback | None = None,
) -> list[FoundJob]:
    """Run profile-driven searches via search_job_postings; returns found_jobs."""
    queries = build_discovery_queries(
        aptitude_profile,
        constraints,
        role_family_plan=role_family_plan,
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
        added = _merge_jobs(found_jobs, seen_urls, search_job_postings(query))
        logger.info(
            "job_discovery query=%r jobs_added=%s total=%s",
            query,
            added,
            len(found_jobs),
        )

    logger.info("job_discovery found_jobs count=%s", len(found_jobs))
    return found_jobs
