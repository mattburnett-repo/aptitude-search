import json
from typing import cast
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.models import Constraints
from app.core.progress import ProgressCallback


@patch("app.core.stream_pipeline.run_pipeline")
def test_stream_pipeline_emits_progress_and_result(
    mock_run_pipeline: MagicMock,
    client: TestClient,
    stage1_fixture: dict[str, object],
    verified_matches_fixture: dict[str, object],
) -> None:
    def fake_pipeline(
        _resume: str,
        _constraints: Constraints | None = None,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> dict[str, object]:
        if on_progress:
            on_progress("Stage 1 starting")
            on_progress("Stage 2 starting")
        return {
            "aptitude_profile": stage1_fixture,
            "verified_matches": verified_matches_fixture,
        }

    mock_run_pipeline.side_effect = fake_pipeline

    with client.stream(
        "POST",
        "/v1/pipeline?stream=1",
        json={"resume": "Jane Doe"},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        assert response.headers.get("cache-control") == "no-cache, no-transform"
        assert response.headers.get("x-accel-buffering") == "no"

        events: list[dict[str, object]] = [
            cast(dict[str, object], json.loads(line))
            for line in response.iter_lines()
            if line.strip()
        ]

    progress = [event for event in events if event["type"] == "progress"]
    results = [event for event in events if event["type"] == "result"]
    assert progress
    assert len(results) == 1
    result_data = cast(dict[str, object], results[0]["data"])
    verified_matches = cast(dict[str, object], result_data["verified_matches"])
    result_rows = cast(list[dict[str, object]], verified_matches["results"])
    assert result_rows[0]["company"] == "Acme Corp"


@patch("app.core.stream_pipeline.run_pipeline")
def test_stream_pipeline_emits_error_event(
    mock_run_pipeline: MagicMock,
    client: TestClient,
) -> None:
    mock_run_pipeline.side_effect = RuntimeError("Pipeline failed")

    with client.stream(
        "POST",
        "/v1/pipeline?stream=1",
        json={"resume": "Jane Doe"},
    ) as response:
        events: list[dict[str, object]] = [
            cast(dict[str, object], json.loads(line))
            for line in response.iter_lines()
            if line.strip()
        ]

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "Pipeline failed" in cast(str, events[0]["detail"])
    assert events[0]["request_id"]
