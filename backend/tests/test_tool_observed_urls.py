"""Tests for spike/notebook tool-observed URL helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

from app.core.json_types import JsonObject

_NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"
if str(_NOTEBOOKS) not in sys.path:
    sys.path.insert(0, str(_NOTEBOOKS))

from tool_observed_urls import (  # noqa: E402  # pyright: ignore[reportImplicitRelativeImport]
    ToolObservedUrlRegistry,
    extract_urls_from_tool_output,
    filter_results_to_tool_observed_urls,
)


def test_extract_urls_from_tool_output_finds_markdown_and_plain_links():
    text = (
        "Found [Acme role](https://acme.com/careers/1) and "
        "also https://beta.com/jobs/2."
    )
    urls = extract_urls_from_tool_output(text)
    assert "https://acme.com/careers/1" in urls
    assert "https://beta.com/jobs/2" in urls


def test_filter_results_to_tool_observed_urls_keeps_only_observed_links():
    registry = ToolObservedUrlRegistry()
    registry.record_url("https://acme.com/careers/1")

    data: JsonObject = {
        "results": [
            {"company": "Acme", "url": "https://acme.com/careers/1"},
            {"company": "Fake", "url": "https://invented.com/jobs/9"},
        ],
        "notes": [],
    }
    filtered = filter_results_to_tool_observed_urls(data, registry)
    filtered_results = cast(list[object], filtered["results"])
    assert len(filtered_results) == 1
    first = cast(JsonObject, filtered_results[0])
    assert first.get("company") == "Acme"
    notes = filtered.get("notes")
    assert isinstance(notes, list)
    note_texts = [str(note) for note in cast(list[object], notes)]
    assert any("Removed 1 result" in note for note in note_texts)
