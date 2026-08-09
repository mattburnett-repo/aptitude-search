"""Stage 3 discovery: Tavily search → junk filter → SERP job rows."""

from __future__ import annotations

import time
from typing import cast

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]
from tavily import TavilyClient  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.job_discovery.url_filters import load_url_filters
from app.job_discovery.url_utils import (
    normalize_job_search_query,
    normalize_result_url,
    should_skip_search_result,
)

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


def _snippet_from_content(content: str) -> str:
    max_chars = config.llm.job_discovery.search_snippet_max_chars
    cleaned = " ".join(content.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def _score_meets_minimum(raw_score: object) -> bool:
    min_score = config.job_discovery.search_min_score
    if min_score <= 0:
        return True
    if not isinstance(raw_score, (int, float)):
        return True
    return float(raw_score) >= min_score


def _tavily_search(query: str, max_results: int) -> list[dict[str, object]]:
    _enforce_rate_limit()
    client = TavilyClient(api_key=config.job_discovery.tavily_api_key)
    filters = load_url_filters()
    exclude_domains = sorted(filters.skip_domains)
    include_domains = sorted(filters.include_domains)
    if include_domains:
        response = cast(
            JsonObject,
            client.search(  # pyright: ignore[reportUnknownMemberType]
                query=query,
                max_results=max_results,
                search_depth=config.job_discovery.search_depth,
                exclude_domains=exclude_domains,
                include_domains=include_domains,
            ),
        )
    else:
        response = cast(
            JsonObject,
            client.search(  # pyright: ignore[reportUnknownMemberType]
                query=query,
                max_results=max_results,
                search_depth=config.job_discovery.search_depth,
                exclude_domains=exclude_domains,
            ),
        )
    rows: list[dict[str, object]] = []
    for item in as_object_list(response.get("results")) or []:
        item_dict = as_object_dict(item)
        if item_dict is None:
            continue
        if not _score_meets_minimum(item_dict.get("score")):
            continue
        rows.append(
            {
                "title": str(item_dict.get("title") or ""),
                "url": str(item_dict.get("url") or ""),
                "content": str(item_dict.get("content") or ""),
                "score": item_dict.get("score"),
            }
        )
    return rows


def _job_from_serp(title: str, url: str, content: str) -> FoundJob | None:
    prepared, error = normalize_result_url(url)
    if error or not prepared:
        return None
    cleaned = title.strip()
    if not cleaned:
        return None
    job: FoundJob = {
        "title": cleaned,
        "company": "",
        "url": prepared,
        "location": "",
    }
    snippet = _snippet_from_content(content)
    if snippet:
        job["snippet"] = snippet
    return job


@traceable(run_type="tool", name="search_job_postings")
def search_job_postings(query: str) -> list[FoundJob]:
    """Run one Tavily search and return job-like SERP rows."""
    search_query = normalize_job_search_query(query)
    max_results = config.llm.job_discovery.search_max_results
    raw_results = _tavily_search(search_query, max_results)

    jobs: list[FoundJob] = []
    for result in raw_results:
        title = str(result.get("title") or "")
        url = str(result.get("url") or result.get("href") or "")
        content = str(result.get("content") or "")
        if should_skip_search_result(url, title=title):
            continue
        job = _job_from_serp(title, url, content)
        if job is not None:
            jobs.append(job)
    return jobs
