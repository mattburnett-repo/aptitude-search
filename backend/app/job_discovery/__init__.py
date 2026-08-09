"""Stage 3 job discovery: profile-driven search and result mapping."""

from app.job_discovery.aptitude_fit import rank_and_filter_found_jobs
from app.job_discovery.discovery import (
    build_discovery_queries,
    run_job_discovery,
)
from app.job_discovery.synthesize_verified_matches import (
    empty_job_discovery_results,
    synthesize_job_discovery_results,
)

__all__ = [
    "empty_job_discovery_results",
    "build_discovery_queries",
    "rank_and_filter_found_jobs",
    "run_job_discovery",
    "synthesize_job_discovery_results",
]
