import logging
from typing import Any

from langsmith import traceable

from app.core import prompt_loader
from app.core.config import config
from app.core.llm import complete_chat_json
from app.core.models import Constraints
from app.core.validate import (
    normalize_aptitude_profile,
    validate_stage,
)
from app.job_discovery import (
    build_stage2_user_message,
    empty_job_discovery_results,
    run_job_discovery_agent,
    synthesize_job_discovery_results,
)
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)
from app.job_discovery.url_utils import filter_found_jobs

logger = logging.getLogger(__name__)

DEFAULT_CONSTRAINTS = Constraints()


@traceable(run_type="chain", name="stage1")
def run_stage1(resume: str) -> Any:
    task = prompt_loader.user_task_stage1()
    user = f"{task}\n\n<resume>\n{resume}\n</resume>"
    result = normalize_aptitude_profile(
        complete_chat_json(
            prompt_loader.system_prompt_stage1(),
            user,
            temperature=config.llm.aptitude.temperature,
        )
    )
    validate_stage("aptitudeProfile", result)
    return result


@traceable(run_type="chain", name="stage2")
def run_stage2(
    aptitude_profile: Any,
    constraints: Constraints | None = None,
) -> Any:
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    user = build_stage2_user_message(aptitude_profile, c)
    tool_observed_urls = ToolObservedUrlRegistry()
    found_jobs = run_job_discovery_agent(
        prompt_loader.system_prompt_stage2_discovery(),
        user,
        max_steps=config.llm.job_discovery.max_steps,
        observed_urls=tool_observed_urls,
    )
    if found_jobs:
        kept = filter_found_jobs(found_jobs)
        removed = len(found_jobs) - len(kept)
        if removed:
            logger.info("stage2 removed %s non-job row(s) from found_jobs", removed)
        found_jobs = kept
    if found_jobs:
        result = synthesize_job_discovery_results(aptitude_profile, c, found_jobs)
        result = filter_results_to_tool_observed_urls(result, tool_observed_urls)
    else:
        result = empty_job_discovery_results(aptitude_profile, c)
    validate_stage("jobDiscovery", result)
    return result


@traceable(run_type="chain", name="pipeline")
def run_pipeline(
    resume: str,
    constraints: Constraints | None = None,
) -> dict[str, Any]:
    aptitude_profile = run_stage1(resume)
    verified_matches = run_stage2(aptitude_profile, constraints)
    return {
        "aptitude_profile": aptitude_profile,
        "verified_matches": verified_matches,
    }
