"""Stage 3 discovery: Tavily search → junk filter → SERP job rows."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from typing import cast

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]
from tavily import TavilyClient  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.job_discovery.url_utils import (
    normalize_job_search_query,
    prepare_scrape_url,
    should_skip_search_result,
)

# Fake search callable for tests (query, max_results) -> SERP rows. Not used at runtime.
SearchFn = Callable[[str, int], Sequence[Mapping[str, object]]]

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


def _tavily_search(query: str, max_results: int) -> list[dict[str, object]]:
    client = TavilyClient(api_key=config.job_discovery.tavily_api_key)
    response = cast(
        JsonObject,
        client.search(query=query, max_results=max_results),  # pyright: ignore[reportUnknownMemberType]
    )
    rows: list[dict[str, object]] = []
    for item in as_object_list(response.get("results")) or []:
        item_dict = as_object_dict(item)
        if item_dict is None:
            continue
        rows.append(
            {
                "title": str(item_dict.get("title") or ""),
                "url": str(item_dict.get("url") or ""),
                "content": str(item_dict.get("content") or ""),
            }
        )
    return rows


def _job_from_serp(title: str, url: str) -> FoundJob | None:
    prepared, error = prepare_scrape_url(url)
    if error or not prepared:
        return None
    cleaned = title.strip()
    if not cleaned:
        return None
    return {
        "title": cleaned,
        "company": "",
        "url": prepared,
        "location": "",
    }


@traceable(run_type="tool", name="search_job_postings")
def search_job_postings(
    query: str,
    *,
    search: SearchFn | None = None,  # optional: pass a fake in tests; leave unset to call Tavily
) -> list[FoundJob]:
    """Run one Tavily search and return job-like SERP rows."""
    search_query = normalize_job_search_query(query)
    max_results = config.llm.job_discovery.search_max_results
    if search is None:
        _enforce_rate_limit()
        raw_results = _tavily_search(search_query, max_results)
    else:
        raw_results = search(search_query, max_results)

    jobs: list[FoundJob] = []
    for result in raw_results:
        title = str(result.get("title") or "")
        url = str(result.get("url") or result.get("href") or "")
        if should_skip_search_result(url, title=title):
            continue
        job = _job_from_serp(title, url)
        if job is not None:
            jobs.append(job)
    return jobs
