"""Stage 2 job discovery: profile-driven search, tools, and synthesis context."""

from app.job_discovery.aptitude_fit import rank_and_filter_found_jobs
from app.job_discovery.context import (
    build_stage2_synthesis_user_message,
    compact_aptitude_profile_summary,
)
from app.job_discovery.discovery import (
    build_discovery_queries,
    run_job_discovery,
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
    "compact_aptitude_profile_summary",
    "empty_job_discovery_results",
    "filter_results_to_tool_observed_urls",
    "build_discovery_queries",
    "rank_and_filter_found_jobs",
    "run_job_discovery",
    "synthesize_job_discovery_results",
]
