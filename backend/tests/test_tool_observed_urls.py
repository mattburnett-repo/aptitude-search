from typing import cast

from app.core.json_types import JsonObject
from app.job_discovery.tool_observed_urls import (
    ToolObservedUrlRegistry,
    extract_urls_from_tool_output,
    filter_results_to_tool_observed_urls,
    normalize_url,
)


def test_normalize_url_strips_www_and_trailing_slash():
    assert (
        normalize_url("https://www.example.com/jobs/1/")
        == "https://example.com/jobs/1"
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
