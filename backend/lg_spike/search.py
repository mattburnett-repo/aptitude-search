"""Spike-local job search: one DDGS backend per call.

Leaves ``app.job_discovery.tools`` unchanged. Used by ``stage3`` fan-out workers.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportImplicitStringConcatenation=false

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable
from typing import Protocol, cast

from smolagents import VisitWebpageTool  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict
from app.job_discovery.page_extract import job_page_dict_for_agent
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.url_utils import (
    is_verified_job_posting,
    looks_like_job_posting_url,
    normalize_job_search_query,
    prepare_scrape_url,
    should_skip_search_result,
)

logger = logging.getLogger(__name__)


class _TextSearchClient(Protocol):
    def text(
        self, query: str, *, max_results: int, backend: str
    ) -> Iterable[dict[str, object]]: ...


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


def _scrape_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
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
    job: dict[str, object] = {
        "title": page["title"],
        "company": page.get("company") or "",
        "url": page["url"],
        "location": page.get("location") or "",
    }
    if not is_verified_job_posting(job):
        return None
    return {
        "title": page["title"],
        "company": page.get("company") or "",
        "url": page["url"],
        "location": page.get("location") or "",
    }


def _ddgs_client() -> _TextSearchClient:
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise ImportError(
            "You must install package `ddgs` to run search: "
            "for instance run `pip install ddgs`."
        ) from exc
    return cast(_TextSearchClient, DDGS())


def search_job_postings(
    query: str,
    *,
    backend: str,
    observed_urls: ToolObservedUrlRegistry | None = None,
) -> JsonObject:
    """Search + scrape for one query on one DDGS backend. Returns jobs payload dict."""
    registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    jd = config.llm.job_discovery
    visit_tool = VisitWebpageTool(max_output_length=jd.visit_max_output_length)
    ddgs = _ddgs_client()

    search_query = normalize_job_search_query(query)
    _ = _enforce_rate_limit(
        rate_limit=jd.search_rate_limit,
        last_request_time=0.0,
    )
    raw_results = list(
        ddgs.text(
            search_query,
            max_results=jd.search_max_results,
            backend=backend,
        )
    )
    if not raw_results:
        return {
            "jobs": [],
            "skipped": 0,
            "message": (
                f"No results for {query!r} via {backend!r}. "
                "Use 3–6 keywords (role + skill + location); drop quotes."
            ),
            "backend": backend,
        }

    rows, skipped = _filter_search_rows(raw_results)
    candidates = _scrape_candidates(rows)
    if not candidates:
        return {
            "jobs": [],
            "skipped": skipped,
            "message": (
                f"No direct job posting URLs for {query!r} via {backend!r}. "
                "Results were list pages, articles, or non-careers links."
            ),
            "backend": backend,
        }

    jobs: list[dict[str, str]] = []
    for row in candidates:
        if len(jobs) >= jd.search_scrape_max:
            break
        page = _scrape_job_page(registry, visit_tool, row["url"])
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

    payload: JsonObject = {
        "jobs": jobs,
        "skipped": skipped,
        "message": message,
        "backend": backend,
    }
    registry.record_tool_output(json.dumps(payload))
    logger.info(
        "lg_search backend=%r query=%r jobs=%s skipped=%s",
        backend,
        query,
        len(jobs),
        skipped,
    )
    return payload


def search_queries_on_backend(
    queries: list[str],
    *,
    backend: str,
) -> tuple[list[FoundJob], list[str]]:
    """Run each query on one backend; return jobs + observed URL list."""
    registry = ToolObservedUrlRegistry()
    found: list[FoundJob] = []
    seen: set[str] = set()
    for query in queries:
        payload = search_job_postings(query, backend=backend, observed_urls=registry)
        jobs_raw = payload.get("jobs")
        if not isinstance(jobs_raw, list):
            continue
        for job in jobs_raw:
            job_dict = as_object_dict(job)
            if job_dict is None:
                continue
            url = str(job_dict.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            found.append(job_dict)
    return found, list(registry.urls)
