"""Shared pytest fixtures. Loads test config before app imports."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Disable LangSmith tracing before app imports (side effect only; discard return value).
_ = os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
_ = os.environ.setdefault("LANGSMITH_TRACING", "false")

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"

sys.path.insert(0, str(BACKEND_DIR))

import app.core.config as config_module # noqa: E402

config_module.config = config_module.Config.load(BACKEND_DIR / "config.test.toml")


@pytest.fixture(autouse=True)
def _mock_input_safety_layers() -> None:
    """Keep tests offline; dedicated tests patch guard/PII behavior explicitly."""
    with (
        patch("app.core.input_safety.resume_chunk_malicious", return_value=False),
        patch("app.core.input_safety._delete_pii", side_effect=lambda text: text),
    ):
        yield


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest.fixture
def stage1_fixture() -> dict[str, object]:
    path = FIXTURES_DIR / "example-outputs" / "career-changer-mixed-stack-stage1.json"
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


@pytest.fixture
def role_family_plan_fixture() -> dict[str, object]:
    path = FIXTURES_DIR / "example-outputs" / "career-changer-role-family-plan.json"
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


@pytest.fixture
def verified_matches_fixture() -> dict[str, object]:
    return {
        "search_plan": [
            "Logistics software companies hiring Django engineers",
            "Integration-heavy SaaS teams with modernization focus",
            "Senior backend roles matching Python and Vue experience",
        ],
        "results": [
            {
                "company": "Acme Corp",
                "role": "Senior Engineer",
                "url": "https://acme.com/careers/senior-engineer",
                "match_description": "Matches Python experience.",
                "location": "Remote",
                "employment_type": "Full-time",
                "seniority_level": "senior",
                "match_signals": ["Python"],
                "confidence": "high",
            }
        ],
        "notes": ["Fixture result."],
    }
