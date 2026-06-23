"""Compact job posting pages for discovery context (full fetch, small return)."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from app.core.config import config
from app.job_discovery.url_utils import looks_like_job_posting_url

_GENERIC_HOST_LABELS = frozenset(
    {"www", "jobs", "careers", "job", "boards", "apply", "wd5"}
)

_BULLET_MAX_CHARS = 200

_META_PREFIXES = (
    "company",
    "employer",
    "organization",
    "location",
    "office",
    "remote",
    "salary",
    "compensation",
    "pay",
    "job type",
    "employment type",
)
_BULLET_LINE = re.compile(r"^(\d+[\.)]\s+|[-*•]\s+)")


def job_page_dict_for_agent(url: str, page_text: str) -> dict[str, str]:
    """Structured scrape fields for discovery tool output (JSON)."""
    text = page_text.strip()
    if not text:
        return {
            "url": url,
            "title": "",
            "company": "",
            "location": "",
            "snippet": "",
            "error": "No page content retrieved.",
        }
    if text.lower().startswith("error fetching"):
        return {
            "url": url,
            "title": "",
            "company": "",
            "location": "",
            "snippet": "",
            "error": text,
        }

    lines = [line.rstrip() for line in text.splitlines()]
    title = _first_heading(lines) or _first_plain_title(lines)
    meta_lines = _meta_lines(lines)
    snippet = _body_snippet(lines, title=title, skip=set(meta_lines))

    company = _meta_field(meta_lines, "company", "employer", "organization")
    if not company and looks_like_job_posting_url(url):
        company = _company_from_url(url)

    return {
        "url": url,
        "title": title,
        "company": company,
        "location": _meta_field(meta_lines, "location", "office", "remote"),
        "snippet": _truncate(snippet, config.llm.job_discovery.page_snippet_max_chars),
        "error": "",
    }


def job_page_json_for_agent(url: str, page_text: str) -> str:
    """JSON string returned by scrape_webpage."""
    return json.dumps(job_page_dict_for_agent(url, page_text))


def compact_job_page_for_agent(url: str, page_text: str) -> str:
    """Return title, metadata, bullets, and a short snippet instead of full page text."""
    fields = job_page_dict_for_agent(url, page_text)
    if fields["error"]:
        return f"URL: {url}\n{fields['error']}"

    parts = [f"URL: {url}"]
    if fields["title"]:
        parts.append(f"Title: {fields['title']}")
    if fields["company"]:
        parts.append(f"company: {fields['company']}")
    if fields["location"]:
        parts.append(f"location: {fields['location']}")
    if fields["snippet"]:
        parts.append(f"Snippet: {fields['snippet']}")

    compact = "\n".join(parts)
    if len(compact) < 200 and page_text.strip():
        compact = f"URL: {url}\n{page_text.strip()[:1500]}"

    return _truncate(compact, config.llm.job_discovery.page_summary_max_chars)


def _first_heading(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def _first_plain_title(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("[", "-", "*", "#")):
            continue
        if len(stripped) <= 120:
            return stripped
    return ""


def _company_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) < 2:
        return ""
    name = labels[-2]
    if name in _GENERIC_HOST_LABELS or len(name) < 3:
        return ""
    return name.replace("-", " ").title()


def _meta_field(meta_lines: list[str], *prefixes: str) -> str:
    for line in meta_lines:
        lower = line.lower()
        for prefix in prefixes:
            if lower.startswith(f"{prefix}:"):
                return line.split(":", 1)[1].strip()
            if lower.startswith(f"{prefix} -"):
                return line.split("-", 1)[1].strip()
    return ""


def _meta_lines(lines: list[str]) -> list[str]:
    found: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(
            lower.startswith(prefix) or f"{prefix}:" in lower or f"{prefix} -" in lower
            for prefix in _META_PREFIXES
        ):
            found.append(stripped[:200])
        if len(found) >= 6:
            break
    return found


def _body_snippet(
    lines: list[str],
    *,
    title: str,
    skip: set[str],
) -> str:
    chunks: list[str] = []
    total = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or _BULLET_LINE.match(stripped):
            continue
        if len(stripped) < 40 or stripped == title or stripped in skip:
            continue
        chunks.append(stripped)
        total += len(stripped)
        if total >= config.llm.job_discovery.page_snippet_max_chars:
            break
    return _truncate(" ".join(chunks), config.llm.job_discovery.page_snippet_max_chars)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
