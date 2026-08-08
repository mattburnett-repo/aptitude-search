import json
from typing import cast

from app.core.json_types import JsonObject
from app.job_discovery.tools import SearchJobPostings


class _StubTavily:
    """Offline Tavily stand-in with canned SERP rows for unit tests."""

    _results: list[dict[str, object]]
    queries: list[tuple[str, int]]

    def __init__(self, results: list[dict[str, object]]) -> None:
        self._results = results
        self.queries = []

    def search(self, query: str, *, max_results: int) -> list[dict[str, object]]:
        self.queries.append((query, max_results))
        return self._results


def _make_search(*, tavily: _StubTavily | None = None) -> SearchJobPostings:
    return SearchJobPostings(
        max_results=10,
        rate_limit=None,
        tavily=tavily or _StubTavily([]),
    )


def _parse_payload(output: str) -> JsonObject:
    return cast(JsonObject, json.loads(output))


def test_search_job_postings_keeps_serp_rows_after_junk_filter() -> None:
    stub = _StubTavily(
        [
            {
                "title": "How to learn Python",
                "href": "https://medium.com/some-article",
                "body": "blog",
            },
            {
                "title": "Backend Engineer",
                "href": "https://acme.com/careers/backend",
                "body": "hiring",
            },
            {
                "title": "Indeed python jobs",
                "href": "https://www.indeed.com/q-python-jobs",
                "body": "list",
            },
        ]
    )
    search = _make_search(tavily=stub)
    output = search.run_search_job_postings("python backend remote")

    payload = _parse_payload(output)
    jobs = cast(list[object], payload.get("jobs"))
    assert len(jobs) == 2
    urls = {cast(JsonObject, job).get("url") for job in jobs}
    assert "https://acme.com/careers/backend" in urls
    assert "https://indeed.com/q-python-jobs" in urls
    assert payload.get("skipped") == 1
    assert stub.queries == [("python backend remote jobs hiring", 10)]


def test_search_job_postings_skips_article_titles() -> None:
    search = _make_search(
        tavily=_StubTavily(
            [
                {
                    "title": "Django vs Node: Complete Guide",
                    "href": "https://somecompany.com/articles/django-vs-node",
                    "body": "comparison",
                },
            ]
        )
    )

    payload = _parse_payload(search.run_search_job_postings("Node.js Django"))
    assert payload.get("jobs") == []
    message = payload.get("message")
    assert isinstance(message, str)
    assert "junk" in message.lower() or "Omitted" in message


def test_search_job_postings_returns_message_when_no_results() -> None:
    search = _make_search(tavily=_StubTavily([]))

    payload = _parse_payload(search.run_search_job_postings("nonsense query xyz"))
    assert payload.get("jobs") == []
    message = payload.get("message")
    assert isinstance(message, str)
    assert "No results" in message
