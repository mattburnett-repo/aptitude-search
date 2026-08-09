from app.job_discovery.tools import search_job_postings


def test_search_job_postings_keeps_serp_rows_after_junk_filter() -> None:
    calls: list[tuple[str, int]] = []

    def search(query: str, max_results: int) -> list[dict[str, object]]:
        calls.append((query, max_results))
        return [
            {
                "title": "How to learn Python",
                "url": "https://medium.com/some-article",
                "content": "blog",
            },
            {
                "title": "Backend Engineer",
                "url": "https://acme.com/careers/backend",
                "content": "hiring",
            },
            {
                "title": "Indeed python jobs",
                "url": "https://www.indeed.com/q-python-jobs",
                "content": "list",
            },
        ]

    jobs = search_job_postings("python backend remote", search=search)

    assert len(jobs) == 2
    urls = {job.get("url") for job in jobs}
    assert "https://acme.com/careers/backend" in urls
    assert "https://indeed.com/q-python-jobs" in urls
    assert calls == [("python backend remote jobs hiring", 10)]


def test_search_job_postings_skips_article_titles() -> None:
    def search(query: str, max_results: int) -> list[dict[str, object]]:
        _ = query, max_results
        return [
            {
                "title": "Django vs Node: Complete Guide",
                "url": "https://somecompany.com/articles/django-vs-node",
                "content": "comparison",
            },
        ]

    jobs = search_job_postings("Node.js Django", search=search)
    assert jobs == []


def test_search_job_postings_returns_empty_when_no_results() -> None:
    def search(query: str, max_results: int) -> list[dict[str, object]]:
        _ = query, max_results
        return []

    assert search_job_postings("nonsense query xyz", search=search) == []
