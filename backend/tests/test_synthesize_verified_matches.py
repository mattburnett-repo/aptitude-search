from typing import cast
from unittest.mock import patch

from app.core.json_types import JsonObject
from app.core.models import Constraints
from app.core.validate import validate_stage
from app.job_discovery.synthesize_verified_matches import (
    empty_job_discovery_results,
    ensure_all_found_jobs_in_results,
    synthesize_job_discovery_results,
)


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


def test_synthesize_calls_llm_and_validates(
    stage1_fixture: dict[str, object],
) -> None:
    found_jobs: list[dict[str, object]] = [
        {
            "title": "Solutions Engineer",
            "company": "Acme",
            "url": "https://acme.com/jobs/1",
        },
    ]
    llm_payload = {
        "search_plan": [
            "Searched solutions engineer roles.",
            "Ranked by aptitude fit.",
            "Mapped profile to role families.",
        ],
        "results": [
            {
                "company": "Acme",
                "role": "Solutions Engineer",
                "url": "https://acme.com/jobs/1",
                "match_description": "Fits adjacent solutions/integration strengths.",
            }
        ],
        "notes": ["Synthesized from found_jobs."],
    }
    with patch(
        "app.job_discovery.synthesize_verified_matches.job_discovery_llm_call",
        return_value=llm_payload,
    ) as mock_llm:
        result = synthesize_job_discovery_results(
            stage1_fixture,
            Constraints(),
            found_jobs,
        )
    mock_llm.assert_called_once()
    validate_stage("jobDiscovery", result)
    results = cast(list[JsonObject], result["results"])
    assert len(results) == 1
    assert "Fits adjacent" in str(results[0]["match_description"])


def test_empty_job_discovery_results_validates(
    stage1_fixture: dict[str, object],
) -> None:
    result = empty_job_discovery_results(stage1_fixture, Constraints())
    validate_stage("jobDiscovery", result)
    assert result["results"] == []
