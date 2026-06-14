from typing import cast
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = cast(dict[str, object], response.json())
    assert body["ok"] is True
    assert body["service"] == "aptitude-search-api"


def test_pipeline_requires_resume(client: TestClient):
    response = client.post("/v1/pipeline", json={"resume": "   "})
    assert response.status_code == 400
    body = cast(dict[str, object], response.json())
    assert body["detail"] == "resume is required"
    assert "request_id" in body
    assert response.headers.get("X-Request-ID")


def test_stage1_requires_resume(client: TestClient):
    response = client.post("/v1/stages/1", json={"resume": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "resume is required"


def test_pipeline_rejects_invalid_constraints(client: TestClient):
    response = client.post(
        "/v1/pipeline",
        json={"resume": "Jane Doe", "constraints": {"remote_preference": "teleport"}},
    )
    assert response.status_code == 422
    body = cast(dict[str, object], response.json())
    assert "detail" in body
    assert "request_id" in body


@patch("app.main.run_pipeline")
def test_pipeline_returns_mocked_result(
    mock_run_pipeline: MagicMock,
    client: TestClient,
    stage1_fixture: dict[str, object],
    verified_matches_fixture: dict[str, object],
):
    mock_run_pipeline.return_value = {
        "aptitude_profile": stage1_fixture,
        "verified_matches": verified_matches_fixture,
    }

    response = client.post("/v1/pipeline", json={"resume": "Jane Doe"})
    assert response.status_code == 200
    body = cast(dict[str, object], response.json())
    aptitude_profile = cast(dict[str, object], body["aptitude_profile"])
    verified_matches = cast(dict[str, object], body["verified_matches"])
    results = cast(list[object], verified_matches["results"])
    assert aptitude_profile["seniority_band"] == "senior"
    assert len(results) == 1


@patch("app.main.run_stage1")
def test_stage1_returns_mocked_profile(
    mock_run_stage1: MagicMock, client: TestClient, stage1_fixture: dict[str, object]
):
    mock_run_stage1.return_value = stage1_fixture
    response = client.post("/v1/stages/1", json={"resume": "Jane Doe"})
    assert response.status_code == 200
    assert response.json()["aptitude_profile"]["seniority_band"] == "senior"


@patch("app.main.run_stage2")
def test_stage2_returns_mocked_matches(
    mock_run_stage2: MagicMock,
    client: TestClient,
    verified_matches_fixture: dict[str, object],
):
    mock_run_stage2.return_value = verified_matches_fixture
    response = client.post(
        "/v1/stages/2",
        json={"aptitude_profile": {"seniority_band": "senior"}, "constraints": None},
    )
    assert response.status_code == 200
    assert response.json()["verified_matches"]["results"][0]["company"] == "Acme Corp"
