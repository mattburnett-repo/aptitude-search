"""Stage 3 discovery: Tavily search → light junk filter → SERP job rows."""

from __future__ import annotations

import json
import time
from typing import Protocol, cast

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import JsonObject, as_object_dict, as_object_list
from app.job_discovery.url_utils import (
    normalize_job_search_query,
    prepare_scrape_url,
    should_skip_search_result,
)


class TavilySearchClient(Protocol):
    """Search surface used by SearchJobPostings (swap-friendly)."""

    def search(self, query: str, *, max_results: int) -> list[dict[str, object]]: ...


class _TavilyHttpClient(Protocol):
    """Subset of ``tavily.TavilyClient`` used by the adapter."""

    def search(self, query: str, *, max_results: int) -> object: ...


class TavilySdkClient:
    """Adapter around ``tavily.TavilyClient`` (search only)."""

    _client: _TavilyHttpClient

    def __init__(self, api_key: str) -> None:
        try:
            from tavily import TavilyClient  # pyright: ignore[reportMissingTypeStubs]
        except ImportError as exc:
            raise ImportError(
                "You must install package `tavily-python` to run this tool: "
                + "for instance run `pip install tavily-python`."
            ) from exc
        self._client = cast(_TavilyHttpClient, cast(object, TavilyClient(api_key=api_key)))

    def search(self, query: str, *, max_results: int) -> list[dict[str, object]]:
        response = cast(JsonObject, self._client.search(query=query, max_results=max_results))
        rows: list[dict[str, object]] = []
        for item in as_object_list(response.get("results")) or []:
            item_dict = as_object_dict(item)
            if item_dict is None:
                continue
            rows.append(
                {
                    "title": str(item_dict.get("title") or ""),
                    "href": str(item_dict.get("url") or ""),
                    "body": str(item_dict.get("content") or ""),
                }
            )
        return rows


def _enforce_rate_limit(
    *,
    rate_limit: float | None,
    last_request_time: float,
) -> float:
    if not rate_limit:
        return last_request_time
    min_interval = 1.0 / rate_limit
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    return time.time()


def _filter_search_rows(
    raw_results: list[dict[str, object]],
) -> tuple[list[dict[str, str]], int]:
    snippet_max = config.llm.job_discovery.search_snippet_max_chars
    rows: list[dict[str, str]] = []
    skipped = 0
    for result in raw_results:
        href = str(result.get("href") or "")
        title = str(result.get("title") or "")
        if should_skip_search_result(href, title=title):
            skipped += 1
            continue
        rows.append(
            {
                "title": title,
                "url": href,
                "snippet": str(result.get("body") or "")[:snippet_max],
            }
        )
    return rows, skipped


def _job_row_from_serp(row: dict[str, str]) -> dict[str, str] | None:
    """Build a found_jobs row from a filtered SERP hit (no page scrape)."""
    prepared, error = prepare_scrape_url(row["url"])
    if error or not prepared:
        return None
    title = (row.get("title") or "").strip()
    if not title:
        return None
    return {
        "title": title,
        "company": "",
        "url": prepared,
        "location": "",
    }


class SearchJobPostings:
    """Search the web and return job-like SERP rows as JSON."""

    max_results: int
    rate_limit: float | None
    _last_request_time: float
    tavily: TavilySearchClient

    def __init__(
        self,
        max_results: int,
        rate_limit: float | None,
        tavily: TavilySearchClient | None = None,
    ) -> None:
        self.max_results = max_results
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self.tavily = tavily or TavilySdkClient(config.job_discovery.tavily_api_key)

    @traceable(run_type="tool", name="search_job_postings")
    def run_search_job_postings(self, query: str) -> str:
        search_query = normalize_job_search_query(query)
        self._last_request_time = _enforce_rate_limit(
            rate_limit=self.rate_limit,
            last_request_time=self._last_request_time,
        )
        raw_results = self.tavily.search(
            search_query,
            max_results=self.max_results,
        )
        if not raw_results:
            return json.dumps(
                {
                    "jobs": [],
                    "skipped": 0,
                    "message": (
                        f"No results for {query!r}. "
                        "Use 3–6 keywords (role + skill + location); drop quotes."
                    ),
                }
            )

        rows, skipped = _filter_search_rows(raw_results)
        jobs: list[dict[str, str]] = []
        for row in rows:
            job = _job_row_from_serp(row)
            if job is None:
                skipped += 1
                continue
            jobs.append(job)

        message = ""
        if skipped:
            message = f"Omitted {skipped} junk or invalid result(s)."
        if not jobs:
            suffix = " No search results passed the junk filter."
            message = (message + suffix).strip()

        return json.dumps({"jobs": jobs, "skipped": skipped, "message": message})


SearchJobPostingsTool = SearchJobPostings


def build_job_discovery_tools() -> list[SearchJobPostings]:
    return [
        SearchJobPostings(
            max_results=config.llm.job_discovery.search_max_results,
            rate_limit=config.llm.job_discovery.search_rate_limit,
        ),
    ]
