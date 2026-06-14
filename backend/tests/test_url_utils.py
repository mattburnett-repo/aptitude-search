from app.job_discovery.url_utils import (
    filter_found_jobs,
    is_verified_job_posting,
    looks_like_job_posting_url,
    prepare_scrape_url,
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


def test_prepare_scrape_url_rejects_unsupported_scheme():
    url, error = prepare_scrape_url("mailto:jobs@example.com")
    assert url is None
    assert error is not None
    assert "Unsupported URL scheme" in error


def test_should_skip_search_result_filters_blog_domains():
    assert should_skip_search_result("https://medium.com/some-article") is True


def test_should_skip_search_result_keeps_careers_page():
    assert (
        should_skip_search_result(
            "https://example.com/careers/software-engineer",
            title="Software Engineer",
        )
        is False
    )


def test_looks_like_job_posting_url_detects_careers_path():
    assert looks_like_job_posting_url("https://example.com/careers/backend") is True


def test_is_verified_job_posting_requires_company_or_job_like_url():
    blog: dict[str, object] = {
        "url": "https://medium.com/post",
        "title": "How to interview",
        "company": "",
    }
    job: dict[str, object] = {
        "url": "https://example.com/careers/backend",
        "title": "Backend Engineer",
        "company": "Example",
    }
    assert is_verified_job_posting(blog) is False
    assert is_verified_job_posting(job) is True


def test_filter_found_jobs_drops_noise():
    jobs: list[dict[str, object]] = [
        {"url": "https://medium.com/post", "title": "Tutorial", "company": ""},
        {
            "url": "https://example.com/jobs/backend",
            "title": "Backend Engineer",
            "company": "Example",
        },
    ]
    kept = filter_found_jobs(jobs)
    assert len(kept) == 1
    assert kept[0]["company"] == "Example"
