from typing import cast

from app.core.json_types import JsonObject
from app.job_discovery.synthesize_verified_matches import ensure_all_found_jobs_in_results


def test_ensure_all_found_jobs_in_results_backfills_omitted_rows() -> None:
    found_jobs: list[dict[str, object]] = [
        {
            "title": "Solutions Engineer",
            "company": "Acme",
            "url": "https://acme.com/jobs/1",
            "aptitude_fit_signals": ["adjacent_role:Solutions Engineer"],
        },
        {
            "title": "Platform Engineer",
            "company": "Beta",
            "url": "https://beta.com/jobs/2",
        },
        {
            "title": "Integration Engineer",
            "company": "Gamma",
            "url": "https://gamma.com/jobs/3",
        },
    ]
    result: JsonObject = {
        "search_plan": ["a", "b", "c"],
        "results": [
            {
                "company": "Acme",
                "role": "Solutions Engineer",
                "url": "https://acme.com/jobs/1",
                "match_description": "LLM wrote this.",
            }
        ],
        "notes": ["Initial note."],
    }

    merged = ensure_all_found_jobs_in_results(result, found_jobs)
    results = cast(list[JsonObject], merged["results"])
    assert len(results) == 3
    urls = {str(row["url"]) for row in results}
    assert urls == {
        "https://acme.com/jobs/1",
        "https://beta.com/jobs/2",
        "https://gamma.com/jobs/3",
    }
    notes = cast(list[str], merged["notes"])
    assert any("Added 2 result(s)" in note for note in notes)
