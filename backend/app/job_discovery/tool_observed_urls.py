"""Track URLs from search_job_postings and filter final results to those URLs."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from app.core.json_types import JsonObject, as_object_dict, as_object_list

_MARKDOWN_LINK_URL = re.compile(r"\]\((https?://[^)\s]+)\)")
_PLAIN_HTTP_URL = re.compile(r"https?://[^\s\)\]>\",']+")


def normalize_url(url: str) -> str:
    """Canonical form for comparing URLs from tools vs model JSON."""
    cleaned = url.strip().rstrip(".,;)")
    if "://" not in cleaned and not cleaned.startswith("//"):
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    if not parsed.scheme or not parsed.netloc:
        return cleaned
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or ""
    return urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))


def extract_urls_from_tool_output(text: str) -> set[str]:
    """Pull http(s) URLs from markdown links and plain text in tool observations."""
    found: set[str] = set()
    for match in _MARKDOWN_LINK_URL.finditer(text):
        found.add(normalize_url(match.group(1)))
    for match in _PLAIN_HTTP_URL.finditer(text):
        found.add(normalize_url(match.group(0)))
    return found


class ToolObservedUrlRegistry:
    """URLs returned by search_job_postings during one discovery run."""

    def __init__(self) -> None:
        self._urls: set[str] = set()

    def record_url(self, url: str) -> None:
        if url and url.strip():
            self._urls.add(normalize_url(url))

    def record_tool_output(self, text: str) -> None:
        self._urls.update(extract_urls_from_tool_output(text))

    def was_observed(self, url: str) -> bool:
        return normalize_url(url) in self._urls

    @property
    def urls(self) -> frozenset[str]:
        return frozenset(self._urls)


def filter_results_to_tool_observed_urls(
    data: JsonObject,
    registry: ToolObservedUrlRegistry,
) -> JsonObject:
    """
    Drop job rows whose url never appeared in tool output (model may invent or alter links).
    """
    results = as_object_list(data.get("results"))
    if results is None:
        return data

    kept: list[JsonObject] = []
    removed = 0
    for item in results:
        row = as_object_dict(item)
        if row is None:
            continue
        url = row.get("url")
        if isinstance(url, str) and registry.was_observed(url):
            kept.append(row)
        else:
            removed += 1

    data["results"] = kept
    if removed:
        notes = as_object_list(data.get("notes"))
        if notes is None:
            notes = []
        notes.append(
            (
                f"Removed {removed} result(s): URL was not present in "
                "search_job_postings tool output."
            )
        )
        data["notes"] = notes
    return data
