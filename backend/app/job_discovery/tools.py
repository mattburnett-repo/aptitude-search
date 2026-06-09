"""Stage 2 agent tools (resilient wrappers around smolagents defaults)."""

from langsmith import traceable
from smolagents import DuckDuckGoSearchTool, VisitWebpageTool

from app.core.config import config
from app.job_discovery.page_extract import compact_job_page_for_agent
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry


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


class ToolOutputObservingVisitWebpageTool(VisitWebpageTool):
    """Records the visited URL and links on the page for post-run filtering."""

    def __init__(
        self,
        observed_urls: ToolObservedUrlRegistry,
        max_output_length: int,
    ) -> None:
        super().__init__(max_output_length=max_output_length)
        self._observed_urls = observed_urls

    def forward(self, url: str) -> str:
        return _run_visit_webpage(self, url)


@traceable(run_type="tool", name="web_search")
def _run_web_search(tool: ResilientWebSearchTool, query: str) -> str:
    tool._enforce_rate_limit()
    results = list(tool.ddgs.text(query, max_results=tool.max_results))
    if not results:
        return (
            "## Search Results\n\n"
            f"No results for: {query!r}. "
            "Use a shorter query (3–6 keywords), drop quotes, or try a different angle."
        )
    snippet_max = config.llm.job_discovery.search_snippet_max_chars
    postprocessed = [
        f"[{result['title']}]({result['href']})\n"
        f"{(result.get('body') or '')[:snippet_max]}"
        for result in results
    ]
    return "## Search Results\n\n" + "\n\n".join(postprocessed)


@traceable(run_type="tool", name="visit_webpage")
def _run_visit_webpage(tool: ToolOutputObservingVisitWebpageTool, url: str) -> str:
    tool._observed_urls.record_url(url)
    output = VisitWebpageTool.forward(tool, url)
    tool._observed_urls.record_tool_output(output)
    return compact_job_page_for_agent(url, output)


def build_job_discovery_tools(
    observed_urls: ToolObservedUrlRegistry,
) -> list[ResilientWebSearchTool | ToolOutputObservingVisitWebpageTool]:
    return [
        ToolOutputObservingWebSearchTool(
            observed_urls,
            max_results=config.llm.job_discovery.search_max_results,
            rate_limit=config.llm.job_discovery.search_rate_limit,
        ),
        ToolOutputObservingVisitWebpageTool(
            observed_urls,
            max_output_length=config.llm.job_discovery.visit_max_output_length,
        ),
    ]
