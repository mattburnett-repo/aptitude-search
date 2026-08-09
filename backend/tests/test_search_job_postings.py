from unittest.mock import MagicMock, patch

from app.core.config import config
from app.job_discovery.tools import _tavily_search, search_job_postings
from app.job_discovery.url_filters import load_url_filters


def test_search_job_postings_keeps_serp_rows_after_junk_filter() -> None:
    serp = [
        {
            "title": "How to learn Python",
            "url": "https://medium.com/some-article",
            "content": "blog",
        },
        {
            "title": "Backend Engineer",
            "url": "https://acme.com/careers/backend",
            "content": "hiring for Django and Vue integrations",
        },
        {
            "title": "Indeed python jobs",
            "url": "https://www.indeed.com/q-python-jobs",
            "content": "list",
        },
    ]
    with patch(
        "app.job_discovery.tools._tavily_search",
        return_value=serp,
    ) as mock_search:
        jobs = search_job_postings("python backend remote")

    assert len(jobs) == 2
    urls = {job.get("url") for job in jobs}
    assert "https://acme.com/careers/backend" in urls
    assert "https://indeed.com/q-python-jobs" in urls
    backend = next(job for job in jobs if job.get("url") == "https://acme.com/careers/backend")
    assert "Django" in str(backend.get("snippet") or "")
    mock_search.assert_called_once_with("python backend remote jobs hiring", 10)


def test_search_job_postings_skips_article_titles() -> None:
    with patch(
        "app.job_discovery.tools._tavily_search",
        return_value=[
            {
                "title": "Django vs Node: Complete Guide",
                "url": "https://somecompany.com/articles/django-vs-node",
                "content": "comparison",
            },
        ],
    ):
        jobs = search_job_postings("Node.js Django")
    assert jobs == []


def test_search_job_postings_returns_empty_when_no_results() -> None:
    with patch("app.job_discovery.tools._tavily_search", return_value=[]):
        assert search_job_postings("nonsense query xyz") == []


def test_tavily_search_passes_depth_exclude_and_score_filter() -> None:
    load_url_filters.cache_clear()
    expected_exclude = sorted(load_url_filters().skip_domains)
    client = MagicMock()
    client.search.return_value = {
        "results": [
            {
                "title": "Low",
                "url": "https://acme.com/jobs/low",
                "content": "x",
                "score": 0.1,
            },
            {
                "title": "High",
                "url": "https://acme.com/jobs/high",
                "content": "y",
                "score": 0.9,
            },
        ]
    }
    with (
        patch("app.job_discovery.tools.TavilyClient", return_value=client),
        patch("app.job_discovery.tools._enforce_rate_limit"),
        patch.object(config.job_discovery, "search_min_score", 0.5),
        patch.object(config.job_discovery, "search_depth", "advanced"),
    ):
        rows = _tavily_search("python jobs", 5)

    assert len(rows) == 1
    assert rows[0]["title"] == "High"
    client.search.assert_called_once_with(
        query="python jobs",
        max_results=5,
        search_depth="advanced",
        exclude_domains=expected_exclude,
    )


def test_tavily_search_passes_include_domains_when_configured() -> None:
    load_url_filters.cache_clear()
    client = MagicMock()
    client.search.return_value = {"results": []}
    with (
        patch("app.job_discovery.tools.TavilyClient", return_value=client),
        patch("app.job_discovery.tools._enforce_rate_limit"),
        patch(
            "app.job_discovery.tools.load_url_filters",
            return_value=MagicMock(
                skip_domains=frozenset({"medium.com"}),
                include_domains=frozenset({"indeed.com", "linkedin.com"}),
            ),
        ),
    ):
        _ = _tavily_search("python jobs", 5)

    kwargs = client.search.call_args.kwargs
    assert kwargs["include_domains"] == ["indeed.com", "linkedin.com"]
    assert kwargs["exclude_domains"] == ["medium.com"]
