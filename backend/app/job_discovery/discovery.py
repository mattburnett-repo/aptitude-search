"""Stage 2a discovery: profile-driven queries + search_job_postings."""

from __future__ import annotations

import json
import logging
from typing import cast

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, JsonValue, as_object_dict, as_object_list
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
    item_list = as_object_list(items)
    if item_list is None:
        return names
    for item in item_list:
        label: str | None = None
        item_dict = as_object_dict(item)
        if item_dict is not None:
            raw = item_dict.get("name") or item_dict.get("label")
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
    aptitude_profile: JsonObject,
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


def _parse_tool_payload(raw: str) -> JsonObject:
    payload = cast(JsonValue, json.loads(raw))
    if not isinstance(payload, dict):
        return {}
    return payload


def _jobs_from_payload(payload: JsonObject) -> list[FoundJob]:
    jobs_raw = as_object_list(payload.get("jobs"))
    if jobs_raw is None:
        return []
    jobs: list[FoundJob] = []
    for job in jobs_raw:
        job_dict = as_object_dict(job)
        if job_dict is not None:
            jobs.append(job_dict)
    return jobs


@traceable(run_type="chain", name="job_discovery")
def run_job_discovery(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    *,
    observed_urls: ToolObservedUrlRegistry | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[FoundJob]:
    """Run profile-driven searches via search_job_postings; returns found_jobs."""
    registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    tool = build_job_discovery_tools(registry)[0]

    queries = build_discovery_queries(aptitude_profile, constraints)
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
        payload = _parse_tool_payload(tool.run_search_job_postings(query))
        typed_jobs = _jobs_from_payload(payload)
        added = _merge_jobs(found_jobs, seen_urls, typed_jobs)
        message = payload.get("message")
        logger.info(
            "job_discovery query=%r jobs_added=%s total=%s message=%r",
            query,
            added,
            len(found_jobs),
            message,
        )

    logger.info("job_discovery found_jobs count=%s", len(found_jobs))
    return found_jobs
