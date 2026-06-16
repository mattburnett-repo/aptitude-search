from app.job_discovery.url_utils import (
    filter_found_jobs,
    is_verified_job_posting,
    looks_like_job_posting_url,
    normalize_job_search_query,
    prepare_scrape_url,
    should_skip_job_title,
    should_skip_search_result,
)


def test_prepare_scrape_url_normalizes_bare_host():
    url, error = prepare_scrape_url("Acme.com/careers/engineer")
    assert error is None
    assert url == "https://acme.com/careers/engineer"


def test_prepare_scrape_url_strips_www_and_trailing_punctuation():
    url, error = prepare_scrape_url("https://www.example.com/jobs/1.")
    assert error is None
    assert url == "https://example.com/jobs/1"


def test_prepare_scrape_url_rejects_placeholder_urls():
    for bad in ("https://...", "http://...", "  https://...  "):
        url, error = prepare_scrape_url(bad)
        assert url is None
        assert error is not None
        assert "Placeholder" in error


def test_prepare_scrape_url_rejects_unsupported_scheme():
    url, error = prepare_scrape_url("mailto:jobs@example.com")
    assert url is None
    assert error is not None
    assert "Unsupported URL scheme" in error


def test_should_skip_search_result_filters_blog_domains():
    assert should_skip_search_result("https://medium.com/some-article") is True


def test_should_skip_search_result_filters_example_domains():
    assert should_skip_search_result("https://example.com/") is True


def test_should_skip_search_result_filters_list_pages():
    assert should_skip_search_result("https://www.indeed.com/q-senior-engineer-jobs") is True
    assert (
        should_skip_search_result(
            "https://www.linkedin.com/jobs/search/?keywords=python"
        )
        is True
    )
    assert should_skip_search_result("https://www.ziprecruiter.com/Jobs/Remote") is True
    assert should_skip_search_result("https://www.upwork.com/freelance-jobs/") is True


def test_should_skip_search_result_keeps_ziprecruiter_job_posting():
    assert (
        should_skip_search_result(
            "https://www.ziprecruiter.com/c/Acme/Job/Senior-Engineer",
            title="Senior Engineer",
        )
        is False
    )
    assert (
        should_skip_search_result(
            "https://acme.com/careers/software-engineer",
            title="Software Engineer",
        )
        is False
    )


def test_looks_like_job_posting_url_detects_careers_path():
    assert looks_like_job_posting_url("https://acme.com/careers/backend") is True


def test_normalize_job_search_query_appends_hiring_keywords():
    assert normalize_job_search_query("Vue Angular") == "Vue Angular jobs hiring"
    assert normalize_job_search_query("senior python careers") == "senior python careers"


def test_should_skip_job_title_rejects_article_headlines():
    assert should_skip_job_title("Node.js vs Django: Complete Guide") is True
    assert should_skip_job_title("Senior Backend Engineer") is False


def test_is_verified_job_posting_requires_job_like_url():
    blog: dict[str, object] = {
        "url": "https://medium.com/post",
        "title": "How to interview",
        "company": "",
    }
    article_with_fake_company: dict[str, object] = {
        "url": "https://geeksforgeeks.org/django-overview",
        "title": "Django Overview",
        "company": "Geeksforgeeks",
    }
    job: dict[str, object] = {
        "url": "https://acme.com/careers/backend",
        "title": "Backend Engineer",
        "company": "Acme",
    }
    assert is_verified_job_posting(blog) is False
    assert is_verified_job_posting(article_with_fake_company) is False
    assert is_verified_job_posting(job) is True


def test_filter_found_jobs_drops_noise():
    jobs: list[dict[str, object]] = [
        {"url": "https://medium.com/post", "title": "Tutorial", "company": ""},
        {
            "url": "https://acme.com/jobs/backend",
            "title": "Backend Engineer",
            "company": "Acme",
        },
    ]
    kept = filter_found_jobs(jobs)
    assert len(kept) == 1
    assert kept[0]["company"] == "Acme"
