from unittest.mock import MagicMock, patch

from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.tools import SearchJobPostingsTool


def _make_tool() -> SearchJobPostingsTool:
    return SearchJobPostingsTool(
        ToolObservedUrlRegistry(),
        max_results=10,
        scrape_max=3,
        rate_limit=None,
        max_output_length=5000,
    )


def test_search_job_postings_filters_list_pages_and_scrapes_candidates() -> None:
    tool = _make_tool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = [
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

    import json

    payload = json.loads(output)
    assert len(payload["jobs"]) == 1
    assert payload["jobs"][0]["company"] == "Acme"
    assert payload["skipped"] == 1
    mock_scrape.assert_called_once()
    assert mock_scrape.call_args.args[2] == "https://acme.com/careers/backend"
    tool.ddgs.text.assert_called_once_with(
        "python backend remote jobs hiring",
        max_results=10,
    )


def test_search_job_postings_skips_non_job_urls_without_scraping() -> None:
    tool = _make_tool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = [
        {
            "title": "Django vs Node",
            "href": "https://somecompany.com/articles/django-vs-node",
            "body": "comparison",
        },
    ]

    with patch("app.job_discovery.tools._scrape_job_page") as mock_scrape:
        import json

        payload = json.loads(tool.run_search_job_postings("Node.js Django"))

    assert payload["jobs"] == []
    assert "No direct job posting URLs" in payload["message"]
    mock_scrape.assert_not_called()


def test_search_job_postings_returns_message_when_no_results() -> None:
    tool = _make_tool()
    tool.ddgs = MagicMock()
    tool.ddgs.text.return_value = []

    import json

    payload = json.loads(tool.run_search_job_postings("nonsense query xyz"))
    assert payload["jobs"] == []
    assert "No results" in payload["message"]
