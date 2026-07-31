import json
from collections.abc import Iterable
from typing import cast
from unittest.mock import patch

from app.core.config import config
from app.core.json_types import JsonObject
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.tools import SearchJobPostingsTool


class _FakeDdgs:
    _results: list[dict[str, object]]

    def __init__(self, results: list[dict[str, object]]) -> None:
        self._results = results
        self.queries: list[tuple[str, int, str]] = []

    def text(
        self, query: str, *, max_results: int, backend: str
    ) -> Iterable[dict[str, object]]:
        self.queries.append((query, max_results, backend))
        return self._results


def _make_tool() -> SearchJobPostingsTool:
    return SearchJobPostingsTool(
        ToolObservedUrlRegistry(),
        max_results=10,
        scrape_max=3,
        rate_limit=None,
        max_output_length=5000,
    )


def _parse_payload(output: str) -> JsonObject:
    return cast(JsonObject, json.loads(output))


def test_search_job_postings_filters_list_pages_and_scrapes_candidates() -> None:
    tool = _make_tool()
    fake_ddgs = _FakeDdgs(
        [
            {
                "title": "Indeed search",
                "href": "https://www.indeed.com/q-python-jobs",
                "body": "list",
            },
            {
                "title": "Backend Engineer",
                "href": "https://acme.com/careers/backend",
                "body": "hiring",
            },
        ]
    )
    tool.ddgs = fake_ddgs

    with patch(
        "app.job_discovery.tools._scrape_job_page",
        return_value={
            "url": "https://acme.com/careers/backend",
            "title": "Backend Engineer",
            "company": "Acme",
            "location": "Remote",
            "snippet": "Build APIs",
            "error": "",
        },
    ) as mock_scrape:
        output = tool.run_search_job_postings("python backend remote")

    payload = _parse_payload(output)
    jobs = cast(list[object], payload.get("jobs"))
    assert len(jobs) == 1
    first_job = cast(JsonObject, jobs[0])
    assert first_job.get("company") == "Acme"
    assert payload.get("skipped") == 1
    mock_scrape.assert_called_once()
    assert mock_scrape.call_args.args[2] == "https://acme.com/careers/backend"
    assert fake_ddgs.queries == [
        (
            "python backend remote jobs hiring",
            10,
            ",".join(config.job_discovery.search_backends),
        )
    ]


def test_search_job_postings_skips_non_job_urls_without_scraping() -> None:
    tool = _make_tool()
    tool.ddgs = _FakeDdgs(
        [
            {
                "title": "Django vs Node",
                "href": "https://somecompany.com/articles/django-vs-node",
                "body": "comparison",
            },
        ]
    )

    with patch("app.job_discovery.tools._scrape_job_page") as mock_scrape:
        payload = _parse_payload(tool.run_search_job_postings("Node.js Django"))

    jobs = payload.get("jobs")
    assert jobs == []
    message = payload.get("message")
    assert isinstance(message, str)
    assert "No direct job posting URLs" in message
    mock_scrape.assert_not_called()


def test_search_job_postings_returns_message_when_no_results() -> None:
    tool = _make_tool()
    tool.ddgs = _FakeDdgs([])

    payload = _parse_payload(tool.run_search_job_postings("nonsense query xyz"))
    assert payload.get("jobs") == []
    message = payload.get("message")
    assert isinstance(message, str)
    assert "No results" in message
