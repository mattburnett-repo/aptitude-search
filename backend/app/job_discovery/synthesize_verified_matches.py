"""Stage 2b: synthesize verified_matches from agent found_jobs.

After the discovery agent (``agent.py``) collects compact job rows via web
search and page scraping, this module runs a single Hugging Face chat call to
map those rows plus the fixed aptitude profile and constraints into
schema-strict ``job-discovery-results`` JSON (``search_plan``, ``results``,
``notes``).

The model does not search the web here; it only formats and verifies postings
already in ``found_jobs``. ``pipeline.run_stage2`` may still drop result URLs
that never appeared in agent tool output (see ``tool_observed_urls.py``).
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from app.core import prompt_loader
from app.job_discovery.context import _labeled_names, build_stage2_synthesis_user_message
from app.core.llm import complete_chat_json
from app.core.models import Constraints
from app.core.validate import normalize_job_discovery_results

_EMPTY_NOTE = (
    "No job postings were found via web search and page scraping "
    "for this profile and constraints."
)


def _location_remote_phrase(constraints: Constraints) -> str:
    parts: list[str] = []
    if constraints.location.strip():
        parts.append(constraints.location.strip())
    if constraints.remote_preference != "any":
        parts.append(constraints.remote_preference)
    return ", ".join(parts) if parts else "open location"


def _build_empty_search_plan(
    profile: dict[str, Any],
    constraints: Constraints,
) -> list[str]:
    plan: list[str] = []
    seniority = profile.get("seniority_band", "unknown")
    skills = _labeled_names(profile.get("core_skills"))
    where = _location_remote_phrase(constraints)

    if skills:
        plan.append(
            f"Searched for {seniority} roles matching core skills ({skills}) in {where}."
        )
    else:
        plan.append(f"Searched for {seniority} roles in {where}.")

    industries = [i.strip() for i in constraints.industries_include if i.strip()]
    if industries:
        plan.append(f"Filtered to industries: {', '.join(industries)}.")

    adjacent = _labeled_names(profile.get("adjacent_roles"))
    if adjacent:
        plan.append(f"Explored adjacent role families: {adjacent}.")

    if constraints.salary_min is not None:
        plan.append(f"Applied minimum salary constraint: ${int(constraints.salary_min):,}.")

    excluded = [i.strip() for i in constraints.industries_exclude if i.strip()]
    if excluded:
        plan.append(f"Excluded industries: {', '.join(excluded)}.")

    while len(plan) < 3:
        plan.append(
            "Ran web search and page scraping; no verified postings met criteria."
        )

    return plan[:8]


@traceable(run_type="chain", name="stage2_empty_results")
def empty_job_discovery_results(
    aptitude_profile: Any,
    constraints: Constraints,
) -> dict[str, Any]:
    """Schema-valid job-discovery-results when the agent found no postings."""
    profile = aptitude_profile if isinstance(aptitude_profile, dict) else {}
    return {
        "search_plan": _build_empty_search_plan(profile, constraints),
        "results": [],
        "notes": [_EMPTY_NOTE],
    }


@traceable(run_type="chain", name="stage2_synthesis")
def synthesize_job_discovery_results(
    aptitude_profile: Any,
    constraints: Constraints,
    found_jobs: list[dict[str, Any]],
) -> Any:
    """Map agent ``found_jobs`` into normalized job-discovery-results dict."""
    user = build_stage2_synthesis_user_message(
        aptitude_profile, constraints, found_jobs
    )
    return normalize_job_discovery_results(
        complete_chat_json(
            prompt_loader.system_prompt_stage2_synthesis(),
            user,
        )
    )
