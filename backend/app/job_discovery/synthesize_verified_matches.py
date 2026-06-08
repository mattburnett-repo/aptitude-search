"""Stage 2b: synthesize verified_matches from agent found_jobs.

After the discovery agent (``agent.py``) collects compact job rows via web
search and page visits, this module runs a single Hugging Face chat call to
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
