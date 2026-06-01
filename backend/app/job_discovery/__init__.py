"""Stage 2 job discovery: agent, tools, and request context."""

from app.job_discovery.agent import run_job_discovery_agent
from app.job_discovery.context import (
    build_stage2_user_message,
    compact_aptitude_profile_summary,
)
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)
from app.job_discovery.tools import ResilientWebSearchTool

__all__ = [
    "ResilientWebSearchTool",
    "ToolObservedUrlRegistry",
    "build_stage2_user_message",
    "compact_aptitude_profile_summary",
    "filter_results_to_tool_observed_urls",
    "run_job_discovery_agent",
]
