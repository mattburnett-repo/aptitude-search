from app.core.profile_text import (
    joined_strings,
    labeled_names,
    profile_labels,
    string_list,
)


def test_profile_labels_extracts_name_and_dedupes() -> None:
    items = [
        {"name": "Python", "confidence": "high"},
        {"label": "Django", "confidence": "high"},
        {"name": "Python", "confidence": "high"},
        "plain string",
    ]
    assert profile_labels(items, limit=10) == ["Python", "Django"]


def test_profile_labels_respects_limit() -> None:
    items = [{"name": f"skill-{i}"} for i in range(5)]
    assert profile_labels(items, limit=2) == ["skill-0", "skill-1"]


def test_labeled_names_joins_profile_labels() -> None:
    items = [{"name": "A"}, {"name": "B"}]
    assert labeled_names(items) == "A, B"


def test_string_list_extracts_plain_strings() -> None:
    items = ["backend engineer", "  ", "platform engineer", "backend engineer", 12]
    assert string_list(items, limit=10) == ["backend engineer", "platform engineer"]


def test_string_list_lowercase() -> None:
    assert string_list(["Backend Engineer"], lowercase=True) == ["backend engineer"]


def test_joined_strings() -> None:
    assert joined_strings(["a", "b"], limit=2) == "a, b"
