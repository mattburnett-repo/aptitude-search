"""Stage 3 synthesis: map ranked found_jobs → verified_matches JSON.

After discovery collects compact job rows via web search and page scraping,
this module runs a single Hugging Face chat call to map those rows plus the
fixed aptitude profile and constraints into schema-strict
``job-discovery-results`` JSON (``search_plan``, ``results``, ``notes``).

The model does not search the web here; it only formats and verifies postings
already in ``found_jobs``. ``pipeline.run_stage3`` may still drop result URLs
that never appeared in tool output (see ``tool_observed_urls.py``).
"""

from __future__ import annotations

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import prompt_loader
from app.core.config import config
from app.job_discovery.context import labeled_names, build_stage3_synthesis_user_message
from app.core.llm import complete_chat_json
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.core.models import Constraints
from app.core.validate import normalize_job_discovery_results
from app.job_discovery.tool_observed_urls import normalize_url

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
    profile: JsonObject,
    constraints: Constraints,
    *,
    role_family_plan: JsonObject | None = None,
) -> list[str]:
    plan: list[str] = []
    seniority = profile.get("seniority_band", "unknown")
    where = _location_remote_phrase(constraints)

    if role_family_plan is not None:
        families = as_object_list(role_family_plan.get("recommended_role_families"))
        family_names: list[str] = []
        if families is not None:
            for family in families:
                family_dict = as_object_dict(family)
                if family_dict is None:
                    continue
                name = family_dict.get("role_family")
                if name:
                    family_names.append(str(name))
        if family_names:
            plan.append(
                f"Mapped aptitude to role families ({', '.join(family_names)}) and searched targeted titles in {where}."
            )

    strengths = labeled_names(profile.get("strengths"), limit=4)
    if strengths:
        plan.append(f"Ranked results by work-pattern fit ({strengths}).")

    adjacent = labeled_names(profile.get("adjacent_roles"))
    if adjacent:
        plan.append(f"Explored adjacent role families: {adjacent}.")

    if not plan:
        skills = labeled_names(profile.get("core_skills"))
        if skills:
            plan.append(
                f"Searched for {seniority} roles matching core skills ({skills}) in {where}."
            )
        else:
            plan.append(f"Searched for {seniority} roles in {where}.")

    industries = [i.strip() for i in constraints.industries_include if i.strip()]
    if industries:
        plan.append(f"Filtered to industries: {', '.join(industries)}.")

    adjacent = labeled_names(profile.get("adjacent_roles"))
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


def _fallback_match_description(job: FoundJob) -> str:
    signals = job.get("aptitude_fit_signals")
    signal_list = as_object_list(signals)
    if signal_list:
        return f"Matched profile signals: {', '.join(str(s) for s in signal_list)}."
    role = job.get("title") or job.get("role") or "role"
    company = job.get("company") or "employer"
    return f"Posting from discovery for {role} at {company}."


def _result_row_from_found_job(job: FoundJob) -> JsonObject:
    location = job.get("location")
    row: JsonObject = {
        "company": str(job.get("company") or "").strip(),
        "role": str(job.get("title") or job.get("role") or "").strip(),
        "url": str(job.get("url") or "").strip(),
        "match_description": _fallback_match_description(job),
    }
    if isinstance(location, str) and location.strip():
        row["location"] = location.strip()
    return row


def ensure_all_found_jobs_in_results(
    result: JsonObject,
    found_jobs: list[FoundJob],
) -> JsonObject:
    """Add any found_jobs rows the synthesis model omitted from results."""
    results_raw = as_object_list(result.get("results"))
    results: list[JsonObject] = []
    if results_raw is not None:
        for item in results_raw:
            row = as_object_dict(item)
            if row is not None:
                results.append(row)
    result["results"] = results

    seen: set[str] = set()
    for row in results:
        url = row.get("url")
        if isinstance(url, str) and url.strip():
            seen.add(normalize_url(url))

    added = 0
    for job in found_jobs:
        url = str(job.get("url") or "").strip()
        if not url:
            continue
        normalized = normalize_url(url)
        if normalized in seen:
            continue
        results.append(_result_row_from_found_job(job))
        seen.add(normalized)
        added += 1

    if added:
        notes = as_object_list(result.get("notes"))
        if notes is None:
            notes = []
        notes.append(
            f"Added {added} result(s) from found_jobs omitted by the synthesis model."
        )
        result["notes"] = notes

    return result


@traceable(run_type="chain", name="stage3_empty_results")
def empty_job_discovery_results(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    *,
    role_family_plan: JsonObject | None = None,
) -> JsonObject:
    """Schema-valid job-discovery-results when discovery found no postings."""
    return {
        "search_plan": _build_empty_search_plan(
            aptitude_profile,
            constraints,
            role_family_plan=role_family_plan,
        ),
        "results": [],
        "notes": [_EMPTY_NOTE],
    }


@traceable(run_type="chain", name="stage3_synthesis")
def synthesize_job_discovery_results(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    found_jobs: list[FoundJob],
    *,
    role_family_plan: JsonObject | None = None,
) -> JsonObject:
    """Map ``found_jobs`` into normalized job-discovery-results dict."""
    user = build_stage3_synthesis_user_message(
        aptitude_profile,
        constraints,
        found_jobs,
        role_family_plan=role_family_plan,
    )
    result = normalize_job_discovery_results(
        complete_chat_json(
            prompt_loader.system_prompt_stage3_synthesis(),
            user,
            temperature=config.llm.job_discovery.temperature,
        )
    )
    return ensure_all_found_jobs_in_results(result, found_jobs)
