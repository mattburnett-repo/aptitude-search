from app.job_discovery.url_filters import load_url_filters
from app.job_discovery.url_utils import (
    normalize_job_search_query,
    normalize_result_url,
    normalize_url,
    should_skip_job_title,
    should_skip_search_result,
)


def test_normalize_result_url_normalizes_bare_host():
    url, error = normalize_result_url("Acme.com/careers/engineer")
    assert error is None
    assert url == "https://acme.com/careers/engineer"


def test_normalize_result_url_strips_www_and_trailing_punctuation():
    url, error = normalize_result_url("https://www.example.com/jobs/1.")
    assert error is None
    assert url == "https://example.com/jobs/1"


def test_normalize_result_url_rejects_placeholder_urls():
    for bad in ("https://...", "http://...", "  https://...  "):
        url, error = normalize_result_url(bad)
        assert url is None
        assert error is not None
        assert "Placeholder" in error


def test_normalize_result_url_rejects_unsupported_scheme():
    url, error = normalize_result_url("mailto:jobs@example.com")
    assert url is None
    assert error is not None
    assert "Unsupported URL scheme" in error


def test_normalize_url_strips_www_and_trailing_slash():
    assert (
        normalize_url("https://www.example.com/jobs/1/")
        == "https://example.com/jobs/1"
    )


def test_should_skip_search_result_filters_blog_domains():
    assert should_skip_search_result("https://medium.com/some-article") is True


def test_should_skip_search_result_filters_example_domains():
    assert should_skip_search_result("https://example.com/") is True


def test_should_skip_search_result_keeps_board_and_careers_urls():
    assert should_skip_search_result("https://www.indeed.com/q-senior-engineer-jobs") is False
    assert (
        should_skip_search_result(
            "https://www.linkedin.com/jobs/search/?keywords=python"
        )
        is False
    )
    assert should_skip_search_result("https://www.upwork.com/freelance-jobs/") is True
    assert (
        should_skip_search_result(
            "https://acme.com/careers/software-engineer",
            title="Software Engineer",
        )
        is False
    )


def test_normalize_job_search_query_appends_hiring_keywords():
    assert normalize_job_search_query("Vue Angular") == "Vue Angular jobs hiring"
    assert normalize_job_search_query("senior python careers") == "senior python careers"


def test_should_skip_job_title_rejects_article_headlines():
    assert should_skip_job_title("Node.js vs Django: Complete Guide") is True
    assert should_skip_job_title("Senior Backend Engineer") is False


def test_url_filters_allow_empty_optional_lists():
    load_url_filters.cache_clear()
    filters = load_url_filters()
    assert filters.skip_domain_suffixes == ()
    assert filters.skip_listing_path_markers == ()
