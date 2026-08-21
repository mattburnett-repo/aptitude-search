from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.core.config import config
from app.job_discovery.listing_gate import exa_search_kwargs
from app.job_discovery.tools import _exa_search, search_job_postings
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
    with (
        patch(
            "app.job_discovery.tools._exa_search",
            return_value=serp,
        ) as mock_search,
        patch("app.job_discovery.listing_gate.url_looks_live", return_value=True),
    ):
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
        "app.job_discovery.tools._exa_search",
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
    with patch("app.job_discovery.tools._exa_search", return_value=[]):
        assert search_job_postings("nonsense query xyz") == []


def test_search_job_postings_drops_urls_that_fail_liveness() -> None:
    serp = [
        {
            "title": "Backend Engineer",
            "url": "https://acme.com/careers/backend",
            "content": "hiring",
        },
        {
            "title": "Gone Role",
            "url": "https://acme.com/careers/gone",
            "content": "was hiring",
        },
    ]

    def _live(url: str) -> bool:
        return "gone" not in url

    with (
        patch("app.job_discovery.tools._exa_search", return_value=serp),
        patch("app.job_discovery.listing_gate.url_looks_live", side_effect=_live),
    ):
        jobs = search_job_postings("python jobs")

    assert len(jobs) == 1
    assert jobs[0]["url"] == "https://acme.com/careers/backend"


def test_exa_search_passes_gate_kwargs() -> None:
    load_url_filters.cache_clear()
    expected = exa_search_kwargs(max_results=5)
    result = MagicMock()
    hit = MagicMock()
    hit.title = "Backend Engineer"
    hit.url = "https://acme.com/jobs/backend"
    hit.highlights = ["hiring for Django"]
    result.results = [hit]
    client = MagicMock()
    client.search.return_value = result
    with (
        patch("app.job_discovery.tools.Exa", return_value=client),
        patch("app.job_discovery.tools._enforce_rate_limit"),
    ):
        rows = _exa_search("python jobs", 5)

    assert len(rows) == 1
    assert rows[0]["title"] == "Backend Engineer"
    assert rows[0]["content"] == "hiring for Django"
    kwargs = client.search.call_args.kwargs
    assert kwargs["type"] == expected["type"]
    assert kwargs["num_results"] == expected["num_results"]
    assert kwargs["contents"] == expected["contents"]
    assert kwargs["exclude_domains"] == expected["exclude_domains"]
    assert kwargs["include_domains"] == expected["include_domains"]
    assert kwargs["start_published_date"] == expected["start_published_date"]
    assert kwargs["start_crawl_date"] == expected["start_crawl_date"]
    assert kwargs["exclude_text"] == expected["exclude_text"]


def test_exa_search_passes_include_domains_when_configured() -> None:
    load_url_filters.cache_clear()
    result = MagicMock()
    result.results = []
    client = MagicMock()
    client.search.return_value = result
    with (
        patch("app.job_discovery.tools.Exa", return_value=client),
        patch("app.job_discovery.tools._enforce_rate_limit"),
        patch(
            "app.job_discovery.listing_gate.load_url_filters",
            return_value=MagicMock(
                skip_domains=frozenset({"medium.com"}),
                include_domains=frozenset({"indeed.com", "linkedin.com"}),
                closed_listing_phrases=("no longer available",),
            ),
        ),
    ):
        _ = _exa_search("python jobs", 5)

    kwargs = client.search.call_args.kwargs
    assert kwargs["include_domains"] == ["indeed.com", "linkedin.com"]
    assert kwargs["exclude_domains"] == ["medium.com"]


def test_search_date_cutoff_uses_configured_max_age_days() -> None:
    days = config.job_discovery.search_max_age_days
    expected_kwargs = exa_search_kwargs(max_results=1)
    if days is None:
        assert expected_kwargs["start_published_date"] is None
        return
    expected = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    assert expected_kwargs["start_published_date"] == expected
