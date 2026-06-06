"""Stage 2 agent tools (resilient wrappers around smolagents defaults)."""

from smolagents import DuckDuckGoSearchTool, VisitWebpageTool

from app.config import config
from app.job_discovery.page_extract import compact_job_page_for_agent
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry


class ResilientWebSearchTool(DuckDuckGoSearchTool):
    """DuckDuckGo search via ddgs; never raises on empty results (keeps the agent loop alive)."""

    def forward(self, query: str) -> str:
        self._enforce_rate_limit()
        results = list(self.ddgs.text(query, max_results=self.max_results))
        if not results:
            return (
                "## Search Results\n\n"
                f"No results for: {query!r}. "
                "Use a shorter query (3–6 keywords), drop quotes, or try a different angle."
            )
        postprocessed = [
            f"[{result['title']}]({result['href']})\n{result['body']}"
            for result in results
        ]
        return "## Search Results\n\n" + "\n\n".join(postprocessed)


class ToolOutputObservingWebSearchTool(ResilientWebSearchTool):
    """Records URLs from search results for post-run filtering of model JSON."""

    def __init__(
        self,
        observed_urls: ToolObservedUrlRegistry,
        max_results: int = 10,
        rate_limit: float | None = 1.0,
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
        self._observed_urls.record_url(url)
        output = super().forward(url)
        self._observed_urls.record_tool_output(output)
        return compact_job_page_for_agent(url, output)


def build_job_discovery_tools(
    observed_urls: ToolObservedUrlRegistry,
) -> list[ResilientWebSearchTool | ToolOutputObservingVisitWebpageTool]:
    return [
        ToolOutputObservingWebSearchTool(observed_urls),
        ToolOutputObservingVisitWebpageTool(
            observed_urls,
            max_output_length=config.llm.job_discovery_visit_max_output_length,
        ),
    ]
