"""URL normalization for scraping and post-search SERP filtering."""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from app.job_discovery.url_filters import load_url_filters

_NON_HTTP_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_JOB_QUERY_HINTS = frozenset(
    {"jobs", "job", "careers", "career", "hiring", "openings", "recruit"}
)
# Spike/page_extract only — production discovery does not gate on these.
_JOB_URL_MARKERS = (
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "myworkdayjobs.com",
    "icims.com",
    "smartrecruiters.com",
    "job-boards.",
    "javascript.jobs",
    "/jobs/",
    "/job/",
    "/careers/",
    "/career/",
    "/hiring/",
)


def _is_placeholder_scrape_url(url: str) -> bool:
    """True for documentation placeholders that must not be scraped."""
    lower = url.strip().lower()
    if "..." in lower or lower.endswith("…"):
        return True
    if lower in {"https://", "http://", "https://...", "http://..."}:
        return True
    return False


def prepare_scrape_url(url: str) -> tuple[str | None, str | None]:
    """
    Normalize a scrape target and reject unsupported schemes.

    Returns ``(normalized_url, error_message)``. ``error_message`` is set when
    the URL cannot be fetched.
    """
    cleaned = url.strip().rstrip(".,;)")
    if not cleaned:
        return None, "Empty URL."

    if _is_placeholder_scrape_url(cleaned):
        return None, (
            "Placeholder URL is not allowed; use URLs from search_job_postings JSON."
        )

    if "://" not in cleaned and not cleaned.startswith("//"):
        scheme_match = _NON_HTTP_SCHEME.match(cleaned)
        if scheme_match:
            scheme = scheme_match.group(0)[:-1].lower()
            return None, (
                f"Unsupported URL scheme {scheme!r}; only http and https are allowed."
            )
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)
    scheme = (parsed.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        return None, (
            f"Unsupported URL scheme {scheme!r}; only http and https are allowed."
        )

    netloc = parsed.netloc.lower()
    if not netloc:
        return None, f"Invalid URL {url!r}: no hostname."

    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parsed.path or ""
    normalized = urlunparse((scheme, netloc, path, "", parsed.query, ""))
    return normalized, None


def normalize_job_search_query(query: str) -> str:
    """Append hiring keywords when a query is skill-only."""
    stripped = " ".join(query.split())
    if not stripped:
        return "software engineer jobs hiring"
    lower = stripped.lower()
    if any(hint in lower for hint in _JOB_QUERY_HINTS):
        return stripped
    return f"{stripped} jobs hiring"


def should_skip_job_title(title: str) -> bool:
    """True when a scraped or SERP title looks like an article, not a role."""
    filters = load_url_filters()
    title_lower = title.lower()
    return any(phrase in title_lower for phrase in filters.skip_title_phrases)


def _host_matches_domain_suffix(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def should_skip_search_result(href: str, *, title: str = "") -> bool:
    """True when a SERP row is unlikely to be a job or careers posting."""
    filters = load_url_filters()
    if not href.strip():
        return True

    prepared, error = prepare_scrape_url(href)
    if error or not prepared:
        return True

    parsed = urlparse(prepared)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path_lower = (parsed.path or "").lower()

    if host in filters.skip_domains:
        return True

    if any(
        _host_matches_domain_suffix(host, domain)
        for domain in filters.skip_domain_suffixes
    ):
        return True

    if host == "github.com" and not any(
        marker in path_lower for marker in ("/jobs", "/careers", "/hiring")
    ):
        return True

    if host.endswith(".dev") and "/docs" in path_lower:
        return True

    if any(marker in path_lower for marker in filters.skip_path_markers):
        return True

    if any(marker in path_lower for marker in filters.skip_listing_path_markers):
        return True

    path_raw = parsed.path or ""
    if any(
        marker in path_raw
        for marker in filters.skip_listing_path_markers_case_sensitive
    ):
        return True

    if should_skip_job_title(title):
        return True

    return False


def looks_like_job_posting_url(url: str) -> bool:
    """True when URL path/host resembles a careers page or ATS posting.

    Kept for spike/page_extract helpers; production search no longer gates on this.
    """
    prepared, error = prepare_scrape_url(url)
    if error or not prepared:
        return False
    lower = prepared.lower()
    return any(marker in lower for marker in _JOB_URL_MARKERS)
