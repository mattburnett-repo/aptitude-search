"""URL normalization and post-search SERP filtering."""

from __future__ import annotations

import re
from urllib.parse import ParseResult, urlparse, urlunparse

from app.job_discovery.url_filters import load_url_filters

_NON_HTTP_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_JOB_QUERY_HINTS = frozenset(
    {"jobs", "job", "careers", "career", "hiring", "openings", "recruit"}
)


def _is_placeholder_url(url: str) -> bool:
    """True for documentation placeholders that are not real result URLs."""
    lower = url.strip().lower()
    if "..." in lower or lower.endswith("…"):
        return True
    if lower in {"https://", "http://", "https://...", "http://..."}:
        return True
    return False


def _clean_url_input(url: str) -> str:
    return url.strip().rstrip(".,;)")


def _ensure_scheme(cleaned: str) -> str:
    if "://" not in cleaned and not cleaned.startswith("//"):
        return f"https://{cleaned}"
    return cleaned


def _format_canonical_url(
    parsed: ParseResult,
    *,
    strip_trailing_slash: bool,
) -> str | None:
    """Lowercase scheme/host, drop www., keep query; None if scheme or host missing."""
    scheme = (parsed.scheme or "").lower()
    netloc = (parsed.netloc or "").lower()
    if not scheme or not netloc:
        return None
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path or ""
    if strip_trailing_slash:
        path = path.rstrip("/") or ""
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def normalize_result_url(url: str) -> tuple[str | None, str | None]:
    """
    Normalize a search-result URL and reject unsupported schemes.

    Returns ``(normalized_url, error_message)``. ``error_message`` is set when
    the URL is invalid for use as a result link.
    """
    cleaned = _clean_url_input(url)
    if not cleaned:
        return None, "Empty URL."

    if _is_placeholder_url(cleaned):
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

    if not parsed.netloc:
        return None, f"Invalid URL {url!r}: no hostname."

    normalized = _format_canonical_url(parsed, strip_trailing_slash=False)
    if normalized is None:
        return None, f"Invalid URL {url!r}: no hostname."
    return normalized, None


def normalize_url(url: str) -> str:
    """Canonical form for comparing URLs (dedupe / merge)."""
    cleaned = _clean_url_input(url)
    if not cleaned:
        return cleaned
    parsed = urlparse(_ensure_scheme(cleaned))
    return _format_canonical_url(parsed, strip_trailing_slash=True) or cleaned


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

    prepared, error = normalize_result_url(href)
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
