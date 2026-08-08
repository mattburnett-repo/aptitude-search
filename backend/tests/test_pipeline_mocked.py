from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from app.core.json_types import JsonObject

from app.core.models import Constraints
from app.core.validate import validate_stage
from app.pipeline import run_pipeline, run_stage3
from app.role_family_plan import Stage2Result


@pytest.fixture
def found_jobs() -> list[dict[str, object]]:
    return [
        {
            "company": "Acme Corp",
            "title": "Senior Engineer",
            "url": "https://acme.com/careers/senior-engineer",
        }
    ]


@patch("app.pipeline.synthesize_job_discovery_results")
@patch("app.pipeline.run_job_discovery")
@patch("app.pipeline.run_stage2")
@patch("app.pipeline.complete_chat_json")
def test_run_pipeline_wires_stages_and_validates_output(
    mock_complete_chat_json: MagicMock,
    mock_run_stage2: MagicMock,
    mock_run_job_discovery: MagicMock,
    mock_synthesize: MagicMock,
    stage1_fixture: dict[str, object],
    role_family_plan_fixture: dict[str, object],
    verified_matches_fixture: dict[str, object],
    found_jobs: list[dict[str, object]],
) -> None:
    mock_complete_chat_json.return_value = stage1_fixture
    mock_run_stage2.return_value = Stage2Result(
        role_family_plan=role_family_plan_fixture,
    )
    mock_run_job_discovery.return_value = found_jobs
    mock_synthesize.return_value = verified_matches_fixture

    result = run_pipeline("Jane Doe resume text", Constraints())

    validate_stage("aptitudeProfile", result["aptitude_profile"])
    validate_stage("roleFamilyPlan", result["role_family_plan"])
    validate_stage("jobDiscovery", result["verified_matches"])
    verified_matches = result["verified_matches"]
    results_raw = verified_matches.get("results")
    assert isinstance(results_raw, list)
    first = cast(JsonObject, results_raw[0])
    assert first.get("company") == "Acme Corp"


@patch("app.pipeline.empty_job_discovery_results")
@patch("app.pipeline.run_job_discovery", return_value=[])
def test_run_stage3_returns_empty_results_when_discovery_finds_nothing(
    _mock_discovery: MagicMock,
    mock_empty_results: MagicMock,
    stage1_fixture: dict[str, object],
) -> None:
    empty: dict[str, object] = {
        "search_plan": [
            "Searched for senior roles matching core skills in open location.",
            "Explored adjacent role families from the aptitude profile.",
            "Ran web search; no verified postings met criteria.",
        ],
        "results": [],
        "notes": ["No job postings were found via web search for this profile and constraints."],
    }
    mock_empty_results.return_value = empty

    result = run_stage3(stage1_fixture, Constraints())
    validate_stage("jobDiscovery", result)
    assert result["results"] == []
