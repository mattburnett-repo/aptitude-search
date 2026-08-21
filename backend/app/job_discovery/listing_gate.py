"""Single listing-rejection gate for Stage 3 discovery.

Criteria lists live in ``url-filters.toml`` (via ``url_filters``). This module is
the only place that decides immediate discards before aptitude-fit / synthesis:

- builds Exa ``search`` kwargs from those criteria + config
- accepts or rejects each SERP row (URL/title junk, closed phrases, live probe)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import cast

import httpx
from exa_py import Exa

from app.core.config import config
from app.core.json_types import FoundJob
from app.job_discovery.url_filters import load_url_filters
from app.job_discovery.url_utils import normalize_result_url, should_skip_search_result

logger = logging.getLogger(__name__)

_DEAD_STATUS_CODES = frozenset({404, 410})
# 503 left out — Cloudflare often uses it for browser challenges.
_SERVER_ERROR_STATUS_CODES = frozenset({500, 502, 504})
_CHALLENGE_STATUS_CODES = frozenset({401, 403, 503})
_MAX_BODY_BYTES = 262_144
_USER_AGENT = "aptitude-search-liveness/1.0"
# Exa API: exclude_text = at most one phrase, each phrase ≤ 5 words.
_EXA_EXCLUDE_TEXT_MAX_PHRASES = 1
_EXA_EXCLUDE_TEXT_MAX_WORDS = 5


def _search_date_cutoff() -> str | None:
    days = config.job_discovery.search_max_age_days
    if days is None:
        return None
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%d")


def _exa_exclude_text(phrases: tuple[str, ...]) -> list[str] | None:
    """Pick Exa-valid exclude_text from closed-listing phrases (post-SERP still uses full list)."""
    chosen: list[str] = []
    for phrase in phrases:
        cleaned = " ".join(phrase.split())
        if not cleaned:
            continue
        if len(cleaned.split()) > _EXA_EXCLUDE_TEXT_MAX_WORDS:
            continue
        chosen.append(cleaned)
        if len(chosen) >= _EXA_EXCLUDE_TEXT_MAX_PHRASES:
            break
    return chosen or None


def run_exa_search(client: Exa, query: str, *, max_results: int) -> list[dict[str, object]]:
    """Run Exa search with gate-derived kwargs; return raw title/url/content rows."""
    filters = load_url_filters()
    include_domains = sorted(filters.include_domains)
    cutoff = _search_date_cutoff()
    exclude_text = _exa_exclude_text(filters.closed_listing_phrases)
    response = client.search(
        query,
        type=config.job_discovery.search_type,
        num_results=max_results,
        contents={"highlights": True},
        exclude_domains=sorted(filters.skip_domains),
        include_domains=include_domains or None,
        start_published_date=cutoff,
        start_crawl_date=cutoff,
        exclude_text=exclude_text,
    )
    rows: list[dict[str, object]] = []
    for item in response.results:
        title = str(item.title or "")
        url = str(item.url or "")
        highlights = getattr(item, "highlights", None)
        if isinstance(highlights, list):
            content = "\n".join(
                part.strip() for part in highlights if isinstance(part, str) and part.strip()
            )
        else:
            content = ""
        rows.append({"title": title, "url": url, "content": content})
    return rows


def exa_search_kwargs(*, max_results: int) -> dict[str, object]:
    """Keyword args for ``Exa.search`` (tests / inspection). Prefer ``run_exa_search``."""
    filters = load_url_filters()
    include_domains = sorted(filters.include_domains)
    cutoff = _search_date_cutoff()
    return {
        "type": config.job_discovery.search_type,
        "num_results": max_results,
        "contents": {"highlights": True},
        "exclude_domains": sorted(filters.skip_domains),
        "include_domains": include_domains or None,
        "start_published_date": cutoff,
        "start_crawl_date": cutoff,
        "exclude_text": _exa_exclude_text(filters.closed_listing_phrases),
    }


def text_looks_closed(text: str) -> bool:
    """True when text matches configured closed-listing phrases."""
    phrases = load_url_filters().closed_listing_phrases
    if not phrases:
        return False
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def _text_has_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    if not markers:
        return False
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def _body_has_markers(body: bytes, markers: tuple[str, ...], *, head_bytes: int) -> bool:
    head = body[:head_bytes].decode("utf-8", errors="ignore")
    return _text_has_any_marker(head, markers)


def _exa_fetch_text(url: str) -> str | None:
    """Fresh page text via Exa when direct HTTP is blocked (e.g. Cloudflare)."""
    try:
        client = Exa(api_key=config.job_discovery.exa_api_key)
        response = client.get_contents(
            [url],
            text=True,
            livecrawl="preferred",
        )
    except Exception as exc:
        logger.info("listing_gate exa_fetch error=%s url=%r", exc, url)
        return None
    results = cast(list[object], list(getattr(response, "results", []) or []))
    if not results:
        return None
    text = str(getattr(results[0], "text", None) or "")
    return text if text.strip() else None


def _page_text_is_dead(text: str) -> bool:
    filters = load_url_filters()
    return (
        text_looks_closed(text)
        or _text_has_any_marker(text, filters.parking_gate_markers)
        or _text_has_any_marker(text, filters.error_page_markers)
    )


def url_looks_live(url: str) -> bool:
    """Return False for clear dead/closed postings; True when unsure or healthy."""
    if not config.job_discovery.url_liveness_check:
        return True

    if should_skip_search_result(url):
        logger.info("listing_gate junk_url url=%r", url)
        return False

    filters = load_url_filters()
    timeout = config.job_discovery.url_liveness_timeout_seconds
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html,*/*"},
        ) as client:
            response = client.get(url)
            final_url = str(response.url)
            if should_skip_search_result(final_url):
                logger.info(
                    "listing_gate junk_final_url url=%r final=%r", url, final_url
                )
                return False
            if (
                response.status_code in _DEAD_STATUS_CODES
                or response.status_code in _SERVER_ERROR_STATUS_CODES
            ):
                logger.info(
                    "listing_gate dead status=%s url=%r",
                    response.status_code,
                    url,
                )
                return False
            body = response.content[:_MAX_BODY_BYTES]
            if _body_has_markers(
                body, filters.parking_gate_markers, head_bytes=8_192
            ) or _body_has_markers(body, filters.error_page_markers, head_bytes=8_192):
                logger.info("listing_gate parking_or_error_page url=%r", url)
                return False
            if text_looks_closed(body.decode("utf-8", errors="ignore")):
                logger.info("listing_gate closed_phrase url=%r", url)
                return False
            challenge_hit = (
                response.status_code in _CHALLENGE_STATUS_CODES
                and _body_has_markers(
                    body, filters.challenge_page_markers, head_bytes=4_096
                )
            )
            if challenge_hit:
                exa_text = _exa_fetch_text(url)
                if exa_text and _page_text_is_dead(exa_text):
                    logger.info("listing_gate exa_closed_phrase url=%r", url)
                    return False
                logger.info(
                    "listing_gate challenge status=%s url=%r exa_checked=%s",
                    response.status_code,
                    url,
                    exa_text is not None,
                )
            return True
    except httpx.HTTPError as exc:
        logger.info("listing_gate http_error=%s url=%r", exc, url)
        exa_text = _exa_fetch_text(url)
        if exa_text and _page_text_is_dead(exa_text):
            logger.info("listing_gate exa_closed_phrase url=%r", url)
            return False
        return True


def _snippet_from_content(content: str) -> str:
    max_chars = config.llm.job_discovery.search_snippet_max_chars
    cleaned = " ".join(content.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def accept_serp_row(
    *,
    title: str,
    url: str,
    content: str,
) -> FoundJob | None:
    """Return a FoundJob if the SERP row passes all rejection criteria; else None."""
    if should_skip_search_result(url, title=title):
        logger.info("listing_gate reject junk_serp url=%r", url)
        return None
    if text_looks_closed(f"{title}\n{content}"):
        logger.info("listing_gate reject closed_serp url=%r", url)
        return None
    prepared, error = normalize_result_url(url)
    if error or not prepared:
        return None
    cleaned = title.strip()
    if not cleaned:
        return None
    if not url_looks_live(prepared):
        logger.info("listing_gate reject stale url=%r", prepared)
        return None
    job: FoundJob = {
        "title": cleaned,
        "company": "",
        "url": prepared,
        "location": "",
    }
    snippet = _snippet_from_content(content)
    if snippet:
        job["snippet"] = snippet
    return job


def filter_serp_rows(rows: list[dict[str, object]]) -> list[FoundJob]:
    """Apply the listing gate to raw SERP rows; only accepted jobs remain."""
    jobs: list[FoundJob] = []
    for row in rows:
        job = accept_serp_row(
            title=str(row.get("title") or ""),
            url=str(row.get("url") or ""),
            content=str(row.get("content") or ""),
        )
        if job is not None:
            jobs.append(job)
    return jobs
