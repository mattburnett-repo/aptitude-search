"""Deterministic Stage 2 discovery: profile-driven queries + search_job_postings."""

from __future__ import annotations

import json
import logging
from typing import Any

from langsmith import traceable

from app.core.config import config
from app.core.models import Constraints
from app.core.progress import ProgressCallback, emit_progress
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.tools import build_job_discovery_tools

logger = logging.getLogger(__name__)

_SKIP_SKILL_NAMES = frozenset(
    {
        "legacy modernization",
        "mentoring",
        "cross-functional communication",
    }
)

_SENIORITY_TO_ROLE = {
    "entry": "junior software engineer",
    "mid": "software engineer",
    "senior": "senior software engineer",
    "staff": "staff software engineer",
    "principal": "principal software engineer",
    "executive": "engineering director",
}


def _skill_names(items: object, *, limit: int) -> list[str]:
    names: list[str] = []
    if not isinstance(items, list):
        return names
    for item in items:
        label: str | None = None
        if isinstance(item, dict):
            raw = item.get("name") or item.get("label")
            if raw:
                label = str(raw).strip()
        elif item:
            label = str(item).strip()
        if not label or label.lower() in _SKIP_SKILL_NAMES:
            continue
        if label not in names:
            names.append(label)
        if len(names) >= limit:
            break
    return names


def _role_label(seniority_band: str) -> str:
    return _SENIORITY_TO_ROLE.get(seniority_band, "software engineer")


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


def build_discovery_queries(
    aptitude_profile: dict[str, Any],
    constraints: Constraints,
    *,
    max_queries: int | None = None,
) -> list[str]:
    """Build hiring-shaped search strings from profile skills and constraints."""
    if max_queries is None:
        max_queries = config.job_discovery.discovery_query_max

    skills = _skill_names(aptitude_profile.get("core_skills"), limit=max_queries)
    if len(skills) < max_queries:
        for name in _skill_names(
            aptitude_profile.get("secondary_skills"),
            limit=max_queries - len(skills),
        ):
            if name not in skills:
                skills.append(name)

    seniority = str(aptitude_profile.get("seniority_band") or "unknown")
    role = _role_label(seniority)
    loc_tokens = _location_tokens(constraints)

    queries: list[str] = []
    for skill in skills[:max_queries]:
        parts = [role, skill, *loc_tokens, "jobs"]
        queries.append(" ".join(parts))
    return queries


def _merge_jobs(
    found_jobs: list[dict[str, Any]],
    seen_urls: set[str],
    new_jobs: list[dict[str, Any]],
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


@traceable(run_type="chain", name="planned_job_discovery")
def run_planned_job_discovery(
    aptitude_profile: Any,
    constraints: Constraints,
    *,
    observed_urls: ToolObservedUrlRegistry | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    """Run profile-planned searches via search_job_postings; returns found_jobs."""
    profile = aptitude_profile if isinstance(aptitude_profile, dict) else {}
    registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    tool = build_job_discovery_tools(registry)[0]

    queries = build_discovery_queries(profile, constraints)
    if not queries:
        logger.warning("planned_discovery built zero queries from profile")
        return []

    found_jobs: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    total = len(queries)

    for index, query in enumerate(queries, start=1):
        emit_progress(
            f"Searching the web ({index}/{total}): {query}…",
            on_progress=on_progress,
        )
        payload = json.loads(tool.run_search_job_postings(query))
        jobs_raw = payload.get("jobs")
        new_jobs = jobs_raw if isinstance(jobs_raw, list) else []
        typed_jobs = [job for job in new_jobs if isinstance(job, dict)]
        added = _merge_jobs(found_jobs, seen_urls, typed_jobs)
        logger.info(
            "planned_discovery query=%r jobs_added=%s total=%s message=%r",
            query,
            added,
            len(found_jobs),
            payload.get("message"),
        )

    logger.info("planned_discovery found_jobs count=%s", len(found_jobs))
    return found_jobs
