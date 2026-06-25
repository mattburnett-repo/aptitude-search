import logging

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import prompt_loader
from app.core.config import config
from app.core.json_types import JsonObject
from app.core.llm import complete_chat_json
from app.core.models import Constraints
from app.core.validate import (
    normalize_aptitude_profile,
    validate_stage,
)
from app.job_discovery import (
    empty_job_discovery_results,
    rank_and_filter_found_jobs,
    run_job_discovery,
    synthesize_job_discovery_results,
)
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)
from app.job_discovery.url_utils import filter_found_jobs
from app.core.progress import ProgressCallback, emit_progress
from app.role_family_plan import run_stage2

logger = logging.getLogger(__name__)

DEFAULT_CONSTRAINTS = Constraints()


@traceable(run_type="chain", name="stage1")
def run_stage1(
    resume: str,
    *,
    on_progress: ProgressCallback | None = None,
) -> JsonObject:
    emit_progress("Stage 1: Building aptitude profile…", on_progress=on_progress)
    task = prompt_loader.user_task_stage1()
    user = f"{task}\n\n<resume>\n{resume}\n</resume>"
    result = normalize_aptitude_profile(
        complete_chat_json(
            prompt_loader.system_prompt_stage1(),
            user,
            temperature=config.llm.aptitude.temperature,
            max_tokens=config.llm.aptitude.max_tokens,
            json_object=True,
        )
    )
    validate_stage("aptitudeProfile", result)
    emit_progress("Stage 1 complete.", on_progress=on_progress)
    return result


@traceable(run_type="chain", name="stage3")
def run_stage3(
    aptitude_profile: JsonObject,
    constraints: Constraints | None = None,
    *,
    role_family_plan: JsonObject | None = None,
    on_progress: ProgressCallback | None = None,
) -> JsonObject:
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    tool_observed_urls = ToolObservedUrlRegistry()
    emit_progress(
        "Stage 3: Searching the web for job postings…",
        on_progress=on_progress,
    )
    found_jobs = run_job_discovery(
        aptitude_profile,
        c,
        role_family_plan=role_family_plan,
        observed_urls=tool_observed_urls,
        on_progress=on_progress,
    )
    if found_jobs:
        emit_progress("Filtering search results…", on_progress=on_progress)
        kept = filter_found_jobs(found_jobs)
        removed = len(found_jobs) - len(kept)
        if removed:
            logger.info("stage3 removed %s non-job row(s) from found_jobs", removed)
        found_jobs = kept
    if found_jobs:
        emit_progress("Ranking by aptitude work-pattern fit…", on_progress=on_progress)
        ranked = rank_and_filter_found_jobs(
            found_jobs,
            aptitude_profile,
            role_family_plan=role_family_plan,
        )
        removed = len(found_jobs) - len(ranked)
        if removed:
            logger.info("stage3 aptitude_fit removed %s low-fit row(s)", removed)
        found_jobs = ranked
    if found_jobs:
        emit_progress(
            f"Found {len(found_jobs)} job posting(s). Synthesizing verified matches…",
            on_progress=on_progress,
        )
        result = synthesize_job_discovery_results(
            aptitude_profile,
            c,
            found_jobs,
            role_family_plan=role_family_plan,
        )
        result = filter_results_to_tool_observed_urls(result, tool_observed_urls)
    else:
        emit_progress(
            "No job postings found; preparing empty results…",
            on_progress=on_progress,
        )
        result = empty_job_discovery_results(
            aptitude_profile,
            c,
            role_family_plan=role_family_plan,
        )
    emit_progress("Validating results…", on_progress=on_progress)
    validate_stage("jobDiscovery", result)
    emit_progress("Stage 3 complete.", on_progress=on_progress)
    return result


@traceable(run_type="chain", name="pipeline")
def run_pipeline(
    resume: str,
    constraints: Constraints | None = None,
    *,
    on_progress: ProgressCallback | None = None,
) -> dict[str, JsonObject]:
    emit_progress("Starting pipeline…", on_progress=on_progress)
    aptitude_profile = run_stage1(resume, on_progress=on_progress)
    role_family_plan = run_stage2(aptitude_profile, on_progress=on_progress)
    verified_matches = run_stage3(
        aptitude_profile,
        constraints,
        role_family_plan=role_family_plan,
        on_progress=on_progress,
    )
    emit_progress("Pipeline complete.", on_progress=on_progress)
    return {
        "aptitude_profile": aptitude_profile,
        "role_family_plan": role_family_plan,
        "verified_matches": verified_matches,
    }
