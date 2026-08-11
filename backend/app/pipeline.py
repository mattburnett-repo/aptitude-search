import json
import logging
from typing import NamedTuple, TypedDict

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import prompt_loader  # sole loader for prompts/ system + user-task files
from app.core.config import config
from app.core.json_types import (
    AptitudeProfile,
    OccupationMatchJson,
    RoleFamilyPlan,
    VerifiedMatches,
)
from app.core.llm import aptitude_llm_call
from app.core.models import Constraints
from app.core.progress import ProgressCallback, emit_progress
from app.core.validate import (
    normalize_aptitude_profile,
    normalize_role_family_plan,
    validate_stage,
)
from app.job_discovery import (
    empty_job_discovery_results,
    rank_and_filter_found_jobs,
    run_job_discovery,
    synthesize_job_discovery_results,
)
from app.onet.match import (
    OccupationMatch,
    format_matches_for_prompt,
    match_aptitude_to_occupations,
)

logger = logging.getLogger(__name__)

DEFAULT_CONSTRAINTS = Constraints()


class PipelineResult(TypedDict):
    aptitude_profile: AptitudeProfile
    role_family_plan: RoleFamilyPlan
    occupation_matches: list[OccupationMatchJson]
    verified_matches: VerifiedMatches


class Stage2Result(NamedTuple):
    role_family_plan: RoleFamilyPlan
    occupation_matches: tuple[OccupationMatch, ...] = ()


@traceable(run_type="chain", name="stage1")
def run_stage1(
    resume: str,
    *,  # keyword-only: callers must pass on_progress=..., not positionally
    on_progress: ProgressCallback | None = None,
) -> AptitudeProfile:
    """Stage 1: resume text → schema-strict aptitude profile.

    - Call the aptitude LLM with the Stage 1 system prompt + resume.
    - Normalize and jsonschema-validate the profile JSON.
    """
    emit_progress("Stage 1: Building aptitude profile…", on_progress=on_progress)
    task = prompt_loader.user_task_stage1()
    user = f"{task}\n\n<resume>\n{resume}\n</resume>"
    result = normalize_aptitude_profile(
        aptitude_llm_call(
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
    aptitude_profile: AptitudeProfile,
    *,  # keyword-only: callers must pass on_progress=..., not positionally
    on_progress: ProgressCallback | None = None,
) -> Stage2Result:
    """Stage 2: aptitude profile → role family plan (+ O*NET matches).

    - Embed the profile and query O*NET occupation vectors (when enabled).
    - Call the aptitude LLM to build a role family plan grounded in those matches.
    - Return ``(role_family_plan, occupation_matches)`` as ``Stage2Result``.
    """
    emit_progress("Stage 2: Accessing career metadata database…", on_progress=on_progress)
    occupation_matches = tuple(match_aptitude_to_occupations(aptitude_profile))
    if occupation_matches:
        emit_progress(
            f"Stage 2: Top career match — {occupation_matches[0].title}.",
            on_progress=on_progress,
        )

    emit_progress("Stage 2: Building role family plan…", on_progress=on_progress)
    task = prompt_loader.user_task_stage2()
    profile_json = json.dumps(aptitude_profile, indent=2)
    onet_block = ""
    if occupation_matches:
        onet_block = (
            "\n\n<onet_occupation_matches>\n"
            f"{format_matches_for_prompt(list(occupation_matches))}\n"
            "Ground recommended_role_families and search_terms in these matches "
            "where they fit the aptitude profile.\n"
            "</onet_occupation_matches>"
        )
    user = (
        f"{task}\n\n<aptitude_profile>\n{profile_json}\n</aptitude_profile>{onet_block}"
    )
    result = normalize_role_family_plan(
        aptitude_llm_call(
            prompt_loader.system_prompt_stage2(),
            user,
            temperature=config.llm.aptitude.temperature,
            max_tokens=config.llm.aptitude.max_tokens,
            json_object=True,
        )
    )
    validate_stage("roleFamilyPlan", result)
    emit_progress("Stage 2 complete.", on_progress=on_progress)
    return Stage2Result(
        role_family_plan=result,
        occupation_matches=occupation_matches,
    )


@traceable(run_type="chain", name="stage3")
def run_stage3(
    aptitude_profile: AptitudeProfile,
    constraints: Constraints | None = None,
    *,  # keyword-only: pass role_family_plan=... / on_progress=..., not positionally
    role_family_plan: RoleFamilyPlan | None = None,
    on_progress: ProgressCallback | None = None,
) -> VerifiedMatches:
    """Stage 3: profile (+ optional plan) → verified job matches.

    - Discover open postings via web search (``run_job_discovery``).
    - Rank/filter by aptitude work-pattern fit.
    - Synthesize schema-strict ``verified_matches`` (or an empty result set).
    """
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    emit_progress(
        "Stage 3: Searching the web for job postings…",
        on_progress=on_progress,
    )
    found_jobs = run_job_discovery(
        aptitude_profile,
        c,
        role_family_plan=role_family_plan,
        on_progress=on_progress,
    )
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
            f"Found {len(found_jobs)} job posting(s). Preparing verified job listings…",
            on_progress=on_progress,
        )
        result = synthesize_job_discovery_results(
            aptitude_profile,
            c,
            found_jobs,
            role_family_plan=role_family_plan,
        )
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
    *,  # keyword-only: callers must pass on_progress=..., not positionally
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    emit_progress("Starting pipeline…", on_progress=on_progress)
    aptitude_profile = run_stage1(resume, on_progress=on_progress)
    role_family_plan, occupation_match_rows = run_stage2(
        aptitude_profile, on_progress=on_progress
    )
    occupation_matches = [match.to_json() for match in occupation_match_rows]
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
        "occupation_matches": occupation_matches,
        "verified_matches": verified_matches,
    }
