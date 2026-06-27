from unittest.mock import MagicMock, patch

import pytest

import app.core.config as config_module
from app.core.json_types import JsonObject
from app.onet.match import OccupationMatch


@pytest.fixture
def onet_matching_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module.config = config_module.config.model_copy(
        update={
            "onet_matching": config_module.config.onet_matching.model_copy(
                update={"enabled": True}
            )
        }
    )


def test_match_aptitude_to_occupations_disabled() -> None:
    from app.onet.match import match_aptitude_to_occupations

    profile: JsonObject = {"aptitude_summary": "Builder who likes ambiguity."}
    assert match_aptitude_to_occupations(profile) == []


@patch("app.core.onet_db.connect")
@patch("app.onet.match.embed_aptitude_profile")
def test_match_aptitude_to_occupations_returns_ranked_matches(
    mock_embed: MagicMock,
    mock_connect: MagicMock,
    onet_matching_enabled: None,
) -> None:
    from app.onet.match import match_aptitude_to_occupations

    mock_embed.return_value = [0.1] * 1024
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("15-1252.00", "Software Developers", "Title: Software Developers", 0.91),
        ("11-3021.00", "Computer and Information Systems Managers", "Title: Managers", 0.72),
    ]
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    cursor_cm.__exit__.return_value = None
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = None
    conn.cursor.return_value = cursor_cm
    mock_connect.return_value = conn

    profile: JsonObject = {
        "aptitude_summary": "Adaptable engineer.",
        "strengths": ["End-to-end ownership"],
        "working_style_signals": ["Pragmatic builder"],
    }
    matches = match_aptitude_to_occupations(profile, top_k=2)

    assert len(matches) == 2
    assert matches[0] == OccupationMatch(
        onetsoc_code="15-1252.00",
        title="Software Developers",
        score=0.91,
        occupation_profile="Title: Software Developers",
    )
    mock_embed.assert_called_once_with(profile)
    cursor.execute.assert_called_once()


@patch("app.role_family_plan.match_aptitude_to_occupations")
@patch("app.role_family_plan.complete_chat_json")
def test_run_stage2_includes_onet_matches_in_prompt(
    mock_complete_chat_json: MagicMock,
    mock_match: MagicMock,
    role_family_plan_fixture: dict[str, object],
) -> None:
    from app.role_family_plan import run_stage2

    mock_match.return_value = [
        OccupationMatch(
            onetsoc_code="15-1252.00",
            title="Software Developers",
            score=0.88,
            occupation_profile="Title: Software Developers\nDescription: Develop software.",
        )
    ]
    mock_complete_chat_json.return_value = role_family_plan_fixture

    result = run_stage2({"aptitude_summary": "Engineer"})

    assert result.role_family_plan == role_family_plan_fixture
    assert len(result.occupation_matches) == 1
    user_prompt = mock_complete_chat_json.call_args.args[1]
    assert "<onet_occupation_matches>" in user_prompt
    assert "Software Developers" in user_prompt
