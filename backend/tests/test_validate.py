import json
from typing import cast

import pytest

from app.core.json_types import JsonObject
from app.core.paths import FIXTURES_DIR
from app.core.validate import (
    normalize_aptitude_profile,
    normalize_job_discovery_results,
    parse_json_response,
    validate_stage,
)


def test_parse_json_response_from_fenced_block():
    raw = 'Here is the profile:\n```json\n{"seniority_band": "mid"}\n```'
    assert parse_json_response(raw) == {"seniority_band": "mid"}


def test_parse_json_response_strips_trailing_commas():
    raw = '{"items": [1, 2,],}'
    assert parse_json_response(raw) == {"items": [1, 2]}


def test_parse_json_response_rejects_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        _ = parse_json_response("not json at all")


def test_normalize_aptitude_profile_maps_seniority_aliases():
    data: JsonObject = {
        "seniority_band": "mid-level",
        "core_skills": [],
        "confidence_map": {},
    }
    result = normalize_aptitude_profile(data)
    assert result["seniority_band"] == "mid"


def test_normalize_aptitude_profile_coerces_inverted_confidence_map():
    data: JsonObject = {
        "seniority_band": "senior",
        "confidence_map": {"high": ["core_skills"], "medium": ["adjacent_roles"]},
    }
    result = normalize_aptitude_profile(data)
    confidence_map = cast(dict[str, dict[str, str]], result["confidence_map"])
    assert confidence_map["core_skills"]["confidence"] == "high"
    assert confidence_map["adjacent_roles"]["confidence"] == "medium"


def test_normalize_job_discovery_results_builds_match_description():
    data: JsonObject = {
        "results": [
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://acme.com/jobs/1",
                "match_signals": ["Python", "Django"],
                "extra_field": "drop-me",
            }
        ]
    }
    result = normalize_job_discovery_results(data)
    results = cast(list[JsonObject], result["results"])
    row = results[0]
    assert row["role"] == "Backend Engineer"
    match_description = cast(str, row["match_description"])
    assert "match signals" in match_description.lower()
    assert "extra_field" not in row


def test_validate_stage_accepts_golden_aptitude_fixture():
    path = FIXTURES_DIR / "career-changer-mixed-stack-stage1.json"
    data = cast(JsonObject, json.loads(path.read_text(encoding="utf-8")))
    normalized = normalize_aptitude_profile(data)
    validate_stage("aptitudeProfile", normalized)


def test_validate_stage_rejects_invalid_constraints():
    with pytest.raises(ValueError, match="Schema validation failed"):
        validate_stage("constraints", {"remote_preference": "teleport"})


def test_validate_stage_unknown_stage_raises():
    with pytest.raises(ValueError, match="Unknown stage"):
        validate_stage("unknown", {})
