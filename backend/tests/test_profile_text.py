from app.core.profile_text import labeled_names, profile_labels


def test_profile_labels_extracts_name_and_dedupes() -> None:
    items = [
        {"name": "Python", "confidence": "high"},
        {"label": "Django", "confidence": "high"},
        {"name": "Python", "confidence": "high"},
        "plain string",
    ]
    assert profile_labels(items, limit=10) == ["Python", "Django", "plain string"]


def test_profile_labels_respects_limit() -> None:
    items = [{"name": f"skill-{i}"} for i in range(5)]
    assert profile_labels(items, limit=2) == ["skill-0", "skill-1"]


def test_labeled_names_joins_profile_labels() -> None:
    items = [{"name": "A"}, {"name": "B"}]
    assert labeled_names(items) == "A, B"
