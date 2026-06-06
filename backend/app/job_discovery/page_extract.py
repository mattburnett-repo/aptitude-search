"""Compact job posting pages for agent context (full fetch, small return)."""

from __future__ import annotations

import re

_AGENT_SUMMARY_MAX_CHARS = 2500
_SNIPPET_MAX_CHARS = 600
_BULLET_MAX_COUNT = 12
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


def compact_job_page_for_agent(url: str, page_text: str) -> str:
    """Return title, metadata, bullets, and a short snippet instead of full page text."""
    text = page_text.strip()
    if not text:
        return f"URL: {url}\n(No page content retrieved.)"

    lines = [line.rstrip() for line in text.splitlines()]

    title = _first_heading(lines) or _first_plain_title(lines)
    meta_lines = _meta_lines(lines)
    bullets = _bullet_lines(lines)
    snippet = _body_snippet(lines, title=title, skip=set(meta_lines))

    parts = [f"URL: {url}"]
    if title:
        parts.append(f"Title: {title}")
    parts.extend(meta_lines)
    if bullets:
        parts.append("Key points:")
        parts.extend(f"- {item}" for item in bullets)
    if snippet:
        parts.append(f"Snippet: {snippet}")

    compact = "\n".join(parts)
    if len(compact) < 200:
        compact = f"URL: {url}\n{text[:1500]}"

    return _truncate(compact, _AGENT_SUMMARY_MAX_CHARS)


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


def _bullet_lines(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or not _BULLET_LINE.match(stripped):
            continue
        item = _BULLET_LINE.sub("", stripped).strip()
        if len(item) < 15 or item in bullets:
            continue
        bullets.append(item[:_BULLET_MAX_CHARS])
        if len(bullets) >= _BULLET_MAX_COUNT:
            break
    return bullets


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
        if total >= _SNIPPET_MAX_CHARS:
            break
    return _truncate(" ".join(chunks), _SNIPPET_MAX_CHARS)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
