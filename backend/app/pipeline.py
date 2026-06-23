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
    run_job_discovery,
    synthesize_job_discovery_results,
)
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)
from app.job_discovery.url_utils import filter_found_jobs
from app.core.progress import ProgressCallback, emit_progress

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


@traceable(run_type="chain", name="stage2")
def run_stage2(
    aptitude_profile: JsonObject,
    constraints: Constraints | None = None,
    *,
    on_progress: ProgressCallback | None = None,
) -> JsonObject:
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    tool_observed_urls = ToolObservedUrlRegistry()
    emit_progress(
        "Stage 2: Searching the web for job postings…",
        on_progress=on_progress,
    )
    found_jobs = run_job_discovery(
        aptitude_profile,
        c,
        observed_urls=tool_observed_urls,
        on_progress=on_progress,
    )
    if found_jobs:
        emit_progress("Filtering search results…", on_progress=on_progress)
        kept = filter_found_jobs(found_jobs)
        removed = len(found_jobs) - len(kept)
        if removed:
            logger.info("stage2 removed %s non-job row(s) from found_jobs", removed)
        found_jobs = kept
    if found_jobs:
        emit_progress(
            f"Found {len(found_jobs)} job posting(s). Synthesizing verified matches…",
            on_progress=on_progress,
        )
        result = synthesize_job_discovery_results(aptitude_profile, c, found_jobs)
        result = filter_results_to_tool_observed_urls(result, tool_observed_urls)
    else:
        emit_progress(
            "No job postings found; preparing empty results…",
            on_progress=on_progress,
        )
        result = empty_job_discovery_results(aptitude_profile, c)
    emit_progress("Validating results…", on_progress=on_progress)
    validate_stage("jobDiscovery", result)
    emit_progress("Stage 2 complete.", on_progress=on_progress)
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
    verified_matches = run_stage2(
        aptitude_profile, constraints, on_progress=on_progress
    )
    emit_progress("Pipeline complete.", on_progress=on_progress)
    return {
        "aptitude_profile": aptitude_profile,
        "verified_matches": verified_matches,
    }
