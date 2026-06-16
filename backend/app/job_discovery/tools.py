"""Stage 2 agent tools (composite search + scrape per query)."""

from __future__ import annotations

import json
import time
from typing import Any

from langsmith import traceable
from smolagents import Tool, VisitWebpageTool

from app.core.config import config
from app.job_discovery.page_extract import job_page_dict_for_agent
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.url_utils import (
    is_verified_job_posting,
    looks_like_job_posting_url,
    normalize_job_search_query,
    prepare_scrape_url,
    should_skip_search_result,
)

_SCRAPE_PER_SEARCH = 3


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
    raw_results: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], int]:
    snippet_max = config.llm.job_discovery.search_snippet_max_chars
    rows: list[dict[str, str]] = []
    skipped = 0
    for result in raw_results:
        href = result.get("href") or ""
        title = result.get("title") or ""
        if should_skip_search_result(href, title=title):
            skipped += 1
            continue
        rows.append(
            {
                "title": title,
                "url": href,
                "snippet": (result.get("body") or "")[:snippet_max],
            }
        )
    return rows, skipped


def _scrape_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Only direct posting/careers URLs are scraped—not generic articles."""
    return [row for row in rows if looks_like_job_posting_url(row["url"])]


def _scrape_job_page(
    observed_urls: ToolObservedUrlRegistry,
    visit_tool: VisitWebpageTool,
    url: str,
) -> dict[str, str]:
    normalized, error = prepare_scrape_url(url)
    if error or not normalized:
        message = error or "Invalid URL."
        return job_page_dict_for_agent(
            url,
            f"Error fetching the webpage: {message}",
        )

    observed_urls.record_url(normalized)
    output = VisitWebpageTool.forward(visit_tool, normalized)
    observed_urls.record_tool_output(output)
    return job_page_dict_for_agent(normalized, output)


def _job_row_from_page(page: dict[str, str]) -> dict[str, str] | None:
    if page.get("error") or not (page.get("title") or "").strip():
        return None
    job: dict[str, str] = {
        "title": page["title"],
        "company": page.get("company") or "",
        "url": page["url"],
        "location": page.get("location") or "",
    }
    if not is_verified_job_posting(job):
        return None
    return job


class SearchJobPostingsTool(Tool):
    """Search, filter SERP rows, and scrape up to three posting URLs per query."""

    name = "search_job_postings"
    description = (
        "Searches the web for job postings matching a query, filters out list pages "
        "and non-job pages, scrapes up to three posting URLs, and returns JSON with "
        "keys jobs (list of title, company, url, location), skipped, and message."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "3–6 keywords: role, skill, and optional location.",
        }
    }
    output_type = "string"

    def __init__(
        self,
        observed_urls: ToolObservedUrlRegistry,
        max_results: int,
        rate_limit: float | None,
        max_output_length: int,
        **kwargs: object,
    ) -> None:
        super().__init__()
        self._observed_urls = observed_urls
        self.max_results = max_results
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._visit_tool = VisitWebpageTool(max_output_length=max_output_length)
        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise ImportError(
                "You must install package `ddgs` to run this tool: "
                "for instance run `pip install ddgs`."
            ) from exc
        self.ddgs = DDGS(**kwargs)

    def forward(self, query: str) -> str:
        return _run_search_job_postings(self, query)


@traceable(run_type="tool", name="search_job_postings")
def _run_search_job_postings(tool: SearchJobPostingsTool, query: str) -> str:
    search_query = normalize_job_search_query(query)
    tool._last_request_time = _enforce_rate_limit(
        rate_limit=tool.rate_limit,
        last_request_time=tool._last_request_time,
    )
    raw_results = list(tool.ddgs.text(search_query, max_results=tool.max_results))
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
    candidates = _scrape_candidates(rows)
    if not candidates:
        return json.dumps(
            {
                "jobs": [],
                "skipped": skipped,
                "message": (
                    f"No direct job posting URLs for {query!r}. "
                    "Results were list pages, articles, or non-careers links."
                ),
            }
        )

    jobs: list[dict[str, str]] = []
    for row in candidates:
        if len(jobs) >= _SCRAPE_PER_SEARCH:
            break
        page = _scrape_job_page(tool._observed_urls, tool._visit_tool, row["url"])
        job = _job_row_from_page(page)
        if job is None:
            continue
        jobs.append(job)

    message = ""
    if skipped:
        message = f"Omitted {skipped} non-posting or list-page result(s)."
    if not jobs:
        suffix = " No scraped pages passed job posting checks."
        message = (message + suffix).strip()

    payload = {"jobs": jobs, "skipped": skipped, "message": message}
    output = json.dumps(payload)
    tool._observed_urls.record_tool_output(output)
    return output


def build_job_discovery_tools(
    observed_urls: ToolObservedUrlRegistry,
) -> list[SearchJobPostingsTool]:
    return [
        SearchJobPostingsTool(
            observed_urls,
            max_results=config.llm.job_discovery.search_max_results,
            rate_limit=config.llm.job_discovery.search_rate_limit,
            max_output_length=config.llm.job_discovery.visit_max_output_length,
        ),
    ]
