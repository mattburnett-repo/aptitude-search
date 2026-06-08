"""Stage 2 phase B: map found_jobs + profile into schema-strict JSON."""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from app import prompt_loader
from app.job_discovery.context import build_stage2_synthesis_user_message
from app.llm import complete_chat_json
from app.models import Constraints
from app.validate import normalize_job_discovery_results


@traceable(run_type="chain", name="stage2_synthesis")
def synthesize_job_discovery_results(
    aptitude_profile: Any,
    constraints: Constraints,
    found_jobs: list[dict[str, Any]],
) -> Any:
    """Single-shot LLM call: found_jobs → job-discovery-results JSON."""
    user = build_stage2_synthesis_user_message(
        aptitude_profile, constraints, found_jobs
    )
    return normalize_job_discovery_results(
        complete_chat_json(
            prompt_loader.system_prompt_stage2_synthesis(),
            user,
        )
    )
