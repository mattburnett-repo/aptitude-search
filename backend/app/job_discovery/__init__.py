"""Stage 2 job discovery: agent, tools, and request context."""

from app.job_discovery.agent import run_job_discovery_agent
from app.job_discovery.context import (
    build_stage2_synthesis_user_message,
    build_stage2_user_message,
    compact_aptitude_profile_summary,
)
from app.job_discovery.planned_discovery import (
    build_discovery_queries,
    run_planned_job_discovery,
)
from app.job_discovery.synthesize_verified_matches import (
    empty_job_discovery_results,
    synthesize_job_discovery_results,
)
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)

__all__ = [
    "ToolObservedUrlRegistry",
    "build_stage2_synthesis_user_message",
    "build_stage2_user_message",
    "compact_aptitude_profile_summary",
    "empty_job_discovery_results",
    "filter_results_to_tool_observed_urls",
    "build_discovery_queries",
    "run_planned_job_discovery",
    "run_job_discovery_agent",
    "synthesize_job_discovery_results",
]
