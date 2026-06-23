from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from app.core.models import Constraints
from app.core.validate import validate_stage
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.pipeline import run_pipeline, run_stage2


@pytest.fixture
def found_jobs() -> list[dict[str, object]]:
    return [
        {
            "company": "Acme Corp",
            "title": "Senior Engineer",
            "url": "https://acme.com/careers/senior-engineer",
        }
    ]


def _passthrough_verified_results(
    data: dict[str, object],
    _registry: ToolObservedUrlRegistry,
) -> dict[str, object]:
    return data


@patch("app.pipeline.synthesize_job_discovery_results")
@patch("app.pipeline.run_planned_job_discovery")
@patch("app.pipeline.complete_chat_json")
def test_run_pipeline_wires_stages_and_validates_output(
    mock_complete_chat_json: MagicMock,
    mock_run_planned_job_discovery: MagicMock,
    mock_synthesize: MagicMock,
    stage1_fixture: dict[str, object],
    verified_matches_fixture: dict[str, object],
    found_jobs: list[dict[str, object]],
) -> None:
    mock_complete_chat_json.return_value = stage1_fixture
    mock_run_planned_job_discovery.return_value = found_jobs
    mock_synthesize.return_value = verified_matches_fixture

    with patch(
        "app.pipeline.filter_results_to_tool_observed_urls",
        side_effect=_passthrough_verified_results,
    ):
        result = run_pipeline("Jane Doe resume text", Constraints())

    validate_stage("aptitudeProfile", result["aptitude_profile"])
    validate_stage("jobDiscovery", result["verified_matches"])
    verified_matches = cast(dict[str, object], result["verified_matches"])
    results = cast(list[dict[str, object]], verified_matches["results"])
    assert results[0]["company"] == "Acme Corp"


@patch("app.pipeline.empty_job_discovery_results")
@patch("app.pipeline.run_planned_job_discovery", return_value=[])
def test_run_stage2_returns_empty_results_when_discovery_finds_nothing(
    _mock_discovery: MagicMock,
    mock_empty_results: MagicMock,
    stage1_fixture: dict[str, object],
) -> None:
    empty: dict[str, object] = {
        "search_plan": [
            "Searched for senior roles matching core skills in open location.",
            "Explored adjacent role families from the aptitude profile.",
            "Ran web search and page scraping; no verified postings met criteria.",
        ],
        "results": [],
        "notes": ["No job postings were found via web search and page scraping."],
    }
    mock_empty_results.return_value = empty

    result = cast(dict[str, object], run_stage2(stage1_fixture, Constraints()))
    validate_stage("jobDiscovery", result)
    assert result["results"] == []
