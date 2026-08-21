"""Stage 3 discovery: Exa search → listing gate → SERP job rows."""

from __future__ import annotations

import time

from exa_py import Exa
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import FoundJob
from app.job_discovery.listing_gate import filter_serp_rows, run_exa_search
from app.job_discovery.url_utils import normalize_job_search_query

_last_request_time = 0.0


def _enforce_rate_limit() -> None:
    global _last_request_time
    rate_limit = config.llm.job_discovery.search_rate_limit
    if not rate_limit:
        return
    min_interval = 1.0 / rate_limit
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_request_time = time.time()


def _exa_search(query: str, max_results: int) -> list[dict[str, object]]:
    _enforce_rate_limit()
    client = Exa(api_key=config.job_discovery.exa_api_key)
    return run_exa_search(client, query, max_results=max_results)


@traceable(run_type="tool", name="search_job_postings")
def search_job_postings(query: str) -> list[FoundJob]:
    """Run one Exa search and return gate-accepted job-like SERP rows."""
    search_query = normalize_job_search_query(query)
    max_results = config.llm.job_discovery.search_max_results
    raw_results = _exa_search(search_query, max_results)
    return filter_serp_rows(raw_results)
