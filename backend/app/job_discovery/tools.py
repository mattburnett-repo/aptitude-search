"""Stage 2 agent tools (resilient wrappers around smolagents defaults)."""

import json

from langsmith import traceable
from smolagents import DuckDuckGoSearchTool, VisitWebpageTool

from app.core.config import config
from app.job_discovery.page_extract import job_page_json_for_agent
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.url_utils import prepare_scrape_url, should_skip_search_result


class ResilientWebSearchTool(DuckDuckGoSearchTool):
    """DuckDuckGo search via ddgs; never raises on empty results (keeps the agent loop alive)."""

    def forward(self, query: str) -> str:
        return _run_web_search(self, query)


class ToolOutputObservingWebSearchTool(ResilientWebSearchTool):
    """Records URLs from search results for post-run filtering of model JSON."""

    def __init__(
        self,
        observed_urls: ToolObservedUrlRegistry,
        max_results: int,
        rate_limit: float | None,
        **kwargs: object,
    ) -> None:
        super().__init__(max_results=max_results, rate_limit=rate_limit, **kwargs)
        self._observed_urls = observed_urls

    def forward(self, query: str) -> str:
        output = super().forward(query)
        self._observed_urls.record_tool_output(output)
        return output


class ToolOutputObservingScrapeWebpageTool(VisitWebpageTool):
    """Records scraped URLs and links on the page for post-run filtering."""

    name = "scrape_webpage"
    description = (
        "Scrapes a job posting URL. Returns a JSON string with keys: "
        "url, title, company, location, snippet, error."
    )

    def __init__(
        self,
        observed_urls: ToolObservedUrlRegistry,
        max_output_length: int,
    ) -> None:
        super().__init__(max_output_length=max_output_length)
        self._observed_urls = observed_urls

    def forward(self, url: str) -> str:
        return _run_scrape_webpage(self, url)


def _search_json(*, results: list[dict[str, str]], skipped: int, message: str) -> str:
    return json.dumps({"results": results, "skipped": skipped, "message": message})


@traceable(run_type="tool", name="web_search")
def _run_web_search(tool: ResilientWebSearchTool, query: str) -> str:
    tool._enforce_rate_limit()
    results = list(tool.ddgs.text(query, max_results=tool.max_results))
    if not results:
        return _search_json(
            results=[],
            skipped=0,
            message=(
                f"No results for {query!r}. "
                "Use 3–6 keywords (role + skill + location); drop quotes."
            ),
        )

    snippet_max = config.llm.job_discovery.search_snippet_max_chars
    rows: list[dict[str, str]] = []
    skipped = 0
    for result in results:
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

    if not rows:
        return _search_json(
            results=[],
            skipped=skipped,
            message=(
                f"No job-relevant results for {query!r}. "
                "Try role + hiring keywords (engineer jobs careers greenhouse lever)."
            ),
        )

    message = ""
    if skipped:
        message = f"Omitted {skipped} documentation/tutorial result(s)."
    return _search_json(results=rows, skipped=skipped, message=message)


@traceable(run_type="tool", name="scrape_webpage")
def _run_scrape_webpage(tool: ToolOutputObservingScrapeWebpageTool, url: str) -> str:
    normalized, error = prepare_scrape_url(url)
    if error or not normalized:
        message = error or "Invalid URL."
        return job_page_json_for_agent(url, f"Error fetching the webpage: {message}")

    tool._observed_urls.record_url(normalized)
    output = VisitWebpageTool.forward(tool, normalized)
    tool._observed_urls.record_tool_output(output)
    return job_page_json_for_agent(normalized, output)


def build_job_discovery_tools(
    observed_urls: ToolObservedUrlRegistry,
) -> list[ResilientWebSearchTool | ToolOutputObservingScrapeWebpageTool]:
    return [
        ToolOutputObservingWebSearchTool(
            observed_urls,
            max_results=config.llm.job_discovery.search_max_results,
            rate_limit=config.llm.job_discovery.search_rate_limit,
        ),
        ToolOutputObservingScrapeWebpageTool(
            observed_urls,
            max_output_length=config.llm.job_discovery.visit_max_output_length,
        ),
    ]
