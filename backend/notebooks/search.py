"""Spike-local job search: one DDGS backend per call.

Leaves ``app.job_discovery.tools`` unchanged. Used by ``stage3`` fan-out workers.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportImplicitStringConcatenation=false

from __future__ import annotations

import json
import logging
import re
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Protocol, cast
from urllib.parse import urlparse

from smolagents import VisitWebpageTool  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import config
from app.core.json_types import FoundJob, JsonObject, as_object_dict
from app.job_discovery.url_utils import (
    normalize_job_search_query,
    normalize_result_url,
)
from job_url_heuristics import (  # pyright: ignore[reportImplicitRelativeImport]
    looks_like_job_posting_url,
)
from page_extract import (  # pyright: ignore[reportImplicitRelativeImport]
    job_page_dict_for_agent,
)
from spike_config import (  # pyright: ignore[reportImplicitRelativeImport]
    SEARCH_SCRAPE_MAX,
    VISIT_MAX_OUTPUT_LENGTH,
)
from tool_observed_urls import (  # pyright: ignore[reportImplicitRelativeImport]
    ToolObservedUrlRegistry,
    extract_urls_from_tool_output,
)

logger = logging.getLogger(__name__)

# Prefer these hosts — VisitWebpageTool can usually scrape them as real postings.
_ATS_SITE_FILTERS = (
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "myworkdayjobs.com",
    "apply.workable.com",
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
)

# Stable family order for round-robin (Greenhouse last so it does not crowd others).
_ATS_FAMILY_ORDER = (
    "lever",
    "ashby",
    "workday",
    "workable",
    "greenhouse",
)

# Hard to scrape from this environment; deprioritize / skip when better options exist.
_HARD_SCRAPE_HOST_SUFFIXES = (
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "glassdoor.co.in",
)

_BLOCKED_TITLE_MARKERS = (
    "recaptcha",
    "checking your browser",
    "access denied",
    "just a moment",
    "cf-browser-verification",
    "attention required",
)

# Setext-style markdown heading used by Lever and others.
_SETEXT_HEADING = re.compile(
    r"^(?P<title>[^\n]{5,120})\n[-=]{3,}\s*$",
    re.MULTILINE,
)


class _TextSearchClient(Protocol):
    def text(
        self, query: str, *, max_results: int, backend: str
    ) -> Iterable[dict[str, object]]: ...


def _enforce_rate_limit(
    *,
    rate_limit: float | None,
    last_request_time: float,
) -> float:
    if not rate_limit:
        return last_request_time
    min_interval = 1.0 / rate_limit
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    return time.time()


def _host(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def _is_hard_scrape_host(url: str) -> bool:
    host = _host(url)
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in _HARD_SCRAPE_HOST_SUFFIXES)


def _ats_family(url: str) -> str:
    """Group related ATS hosts so Greenhouse variants share one quota."""
    lower = url.lower()
    if "greenhouse.io" in lower:
        return "greenhouse"
    if "lever.co" in lower:
        return "lever"
    if "ashbyhq.com" in lower:
        return "ashby"
    if "myworkdayjobs.com" in lower:
        return "workday"
    if "workable.com" in lower:
        return "workable"
    return _host(url) or "other"


def _max_jobs_per_ats_family(scrape_max: int) -> int:
    """Cap per ATS family so one board cannot fill the whole scrape budget."""
    return max(1, (scrape_max + 2) // 3)


def _is_ats_url(url: str) -> bool:
    lower = url.lower()
    return any(site in lower for site in _ATS_SITE_FILTERS)


def _is_individual_posting_url(url: str) -> bool:
    """True for a single ATS/job posting URL (not a board index or SERP list)."""
    prepared, error = normalize_result_url(url)
    if error or not prepared:
        return False
    lower = prepared.lower()
    path = urlparse(prepared).path.lower()

    if "greenhouse.io" in lower and re.search(r"/jobs/\d+", path):
        return True
    if "jobs.lever.co" in lower and re.search(
        r"^/[^/]+/[0-9a-f]{8}-[0-9a-f-]{27}", path
    ):
        return True
    if "ashbyhq.com" in lower and re.search(r"^/[^/]+/[0-9a-f-]{8,}", path):
        return True
    if "myworkdayjobs.com" in lower and "/job/" in path:
        return True
    if "workable.com" in lower and re.search(r"/j/[a-z0-9]+", path):
        return True
    return False


def _is_unusable_serp_row(href: str, _title: str) -> bool:
    """Drop only empty/invalid URLs (spike keeps list pages for follow-up extract)."""
    if not href.strip():
        return True
    prepared, error = normalize_result_url(href)
    if error or not prepared:
        return True
    return False


def _filter_search_rows(
    raw_results: list[dict[str, object]],
) -> tuple[list[dict[str, str]], int]:
    snippet_max = config.llm.job_discovery.search_snippet_max_chars
    rows: list[dict[str, str]] = []
    skipped = 0
    for result in raw_results:
        href = str(result.get("href") or "")
        title = str(result.get("title") or "")
        if _is_unusable_serp_row(href, title):
            skipped += 1
            continue
        rows.append(
            {
                "title": title,
                "url": href,
                "snippet": str(result.get("body") or "")[:snippet_max],
            }
        )
    return rows, skipped


def _candidate_sort_key(row: dict[str, str]) -> tuple[int, int, int, int]:
    """Lower is better: individual ATS postings first, hard-scrape hosts last."""
    url = row["url"]
    return (
        0 if _is_individual_posting_url(url) else 1,
        0 if _is_ats_url(url) else 1,
        0 if looks_like_job_posting_url(url) else 1,
        1 if _is_hard_scrape_host(url) else 0,
    )


def _scrape_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Quality-sort within each ATS family, then round-robin across families."""
    ranked = sorted(rows, key=_candidate_sort_key)
    buckets: dict[str, deque[dict[str, str]]] = defaultdict(deque)
    for row in ranked:
        buckets[_ats_family(row["url"])].append(row)

    family_order = [name for name in _ATS_FAMILY_ORDER if name in buckets]
    family_order.extend(sorted(name for name in buckets if name not in _ATS_FAMILY_ORDER))

    out: list[dict[str, str]] = []
    while any(buckets[name] for name in family_order):
        for name in family_order:
            if buckets[name]:
                out.append(buckets[name].popleft())
    return out


def _looks_like_board_listing_page(raw_text: str) -> bool:
    """True when a posting URL actually returned a multi-job board page."""
    lower = raw_text.lower()
    if "current openings" in lower or "create a job alert" in lower:
        return True
    if lower.count("/jobs/") >= 3 and "apply" not in lower[:500]:
        return True
    return False


def _is_blocked_page(page: dict[str, str], raw_text: str) -> bool:
    if page.get("error"):
        return True
    blob = f"{page.get('title') or ''}\n{raw_text}".lower()
    return any(marker in blob for marker in _BLOCKED_TITLE_MARKERS)


def _is_weak_title(title: str) -> bool:
    text = title.strip()
    if not text or len(text) < 4 or len(text) > 120:
        return True
    if re.fullmatch(r"[\W_\s]+", text):
        return True
    lower = text.lower()
    if lower.endswith(":"):
        return True
    if lower.startswith(
        (
            "some examples",
            "you need to enable",
            "current openings",
            "jobs at ",
            "search ",
            "create a job",
            "job alert",
            "sign in",
            "log in",
            "level-up your career",
            "level up your career",
        )
    ):
        return True
    # Marketing / sentence titles, not role names.
    if text.endswith(".") and len(text) > 60:
        return True
    if lower in {
        "analysis",
        "overview",
        "about",
        "description",
        "apply",
        "search",
        "create a job alert",
    }:
        return True
    if any(marker in lower for marker in _BLOCKED_TITLE_MARKERS):
        return True
    return False


def _title_from_markdown(raw_text: str) -> str:
    """Prefer setext headings / first strong line over mis-parsed body headings."""
    match = _SETEXT_HEADING.search(raw_text)
    if match:
        title = match.group("title").strip()
        if not _is_weak_title(title) and not re.fullmatch(r"[-=]+", title):
            return title

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("![", "[!", "[", "<", "http://", "https://")):
            continue
        if re.fullmatch(r"[-=]{3,}", stripped):
            continue
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        # "Employer - Role" first line on Lever pages.
        if " - " in stripped and not _is_weak_title(stripped):
            return stripped
        if not _is_weak_title(stripped):
            return stripped
    return ""


def _company_from_ats_url(url: str) -> str:
    prepared, error = normalize_result_url(url)
    if error or not prepared:
        return ""
    host = _host(prepared)
    parts = [p for p in urlparse(prepared).path.split("/") if p]
    slug = ""
    if "lever.co" in host and parts:
        slug = parts[0]
    elif "greenhouse.io" in host and parts:
        slug = parts[0]
    elif "ashbyhq.com" in host and parts:
        slug = parts[0]
    if not slug or slug in {"jobs", "embed", "job"}:
        return ""
    return slug.replace("-", " ").replace("_", " ").title()


def _posting_urls_from_page_text(raw_text: str, *, source_url: str) -> list[str]:
    """Pull job-like links out of a scraped board/list page."""
    found: list[str] = []
    seen: set[str] = set()
    for url in extract_urls_from_tool_output(raw_text):
        if url in seen or url.rstrip("/") == source_url.rstrip("/"):
            continue
        if not (_is_individual_posting_url(url) or looks_like_job_posting_url(url)):
            continue
        seen.add(url)
        found.append(url)
    return found


def _scrape_job_page(
    observed_urls: ToolObservedUrlRegistry,
    visit_tool: VisitWebpageTool,
    url: str,
) -> tuple[dict[str, str], str]:
    normalized, error = normalize_result_url(url)
    if error or not normalized:
        message = error or "Invalid URL."
        raw = f"Error fetching the webpage: {message}"
        return job_page_dict_for_agent(url, raw), raw

    observed_urls.record_url(normalized)
    raw = VisitWebpageTool.forward(visit_tool, normalized)
    observed_urls.record_tool_output(raw)
    return job_page_dict_for_agent(normalized, raw), raw


def _job_row_from_page(
    page: dict[str, str],
    raw_text: str,
    *,
    serp_title: str = "",
) -> dict[str, str] | None:
    """Keep scrapes with a usable title (any host — not ATS-only)."""
    if page.get("error"):
        return None

    title = _title_from_markdown(raw_text)
    if _is_weak_title(title):
        title = (page.get("title") or "").strip()
    if _is_weak_title(title) and serp_title.strip():
        title = serp_title.strip()
    if _is_weak_title(title):
        return None

    company = _company_from_ats_url(page["url"])
    scraped_company = (page.get("company") or "").strip()
    if scraped_company and scraped_company.lower() not in {
        "lever",
        "greenhouse",
        "ashby",
        "ashbyhq",
        "workday",
        "workable",
    }:
        company = scraped_company
    if not company:
        company = scraped_company

    return {
        "title": title,
        "company": company,
        "url": page["url"],
        "location": page.get("location") or "",
    }


def _ddgs_client() -> _TextSearchClient:
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise ImportError(
            "You must install package `ddgs` to run search: "
            "for instance run `pip install ddgs`."
        ) from exc
    return cast(_TextSearchClient, DDGS())


def _ddgs_text(
    ddgs: _TextSearchClient,
    *,
    query: str,
    max_results: int,
    backend: str,
) -> list[dict[str, object]]:
    return list(
        ddgs.text(
            query,
            max_results=max_results,
            backend=backend,
        )
    )


def search_job_postings(
    query: str,
    *,
    backend: str,
    observed_urls: ToolObservedUrlRegistry | None = None,
) -> JsonObject:
    """Search + scrape for one query on one DDGS backend. Returns jobs payload dict."""
    registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    visit_tool = VisitWebpageTool(max_output_length=VISIT_MAX_OUTPUT_LENGTH)
    ddgs = _ddgs_client()
    jd = config.llm.job_discovery

    search_query = normalize_job_search_query(query)
    _ = _enforce_rate_limit(
        rate_limit=jd.search_rate_limit,
        last_request_time=0.0,
    )

    try:
        raw_results = _ddgs_text(
            ddgs,
            query=search_query,
            max_results=jd.search_max_results,
            backend=backend,
        )
    except Exception as exc:
        logger.warning(
            "lg_search backend=%r query=%r failed: %s",
            backend,
            search_query,
            exc,
        )
        return {
            "jobs": [],
            "skipped": 0,
            "message": f"Search failed for {query!r} via {backend!r}: {exc}",
            "backend": backend,
        }

    if not raw_results:
        return {
            "jobs": [],
            "skipped": 0,
            "message": (
                f"No results for {query!r} via {backend!r}. "
                "Use 3–6 keywords (role + skill + location); drop quotes."
            ),
            "backend": backend,
        }

    rows, skipped = _filter_search_rows(raw_results)
    candidates = _scrape_candidates(rows)
    if not candidates:
        return {
            "jobs": [],
            "skipped": skipped,
            "message": (
                f"No scrape candidates for {query!r} via {backend!r} "
                f"after soft filter (skipped={skipped})."
            ),
            "backend": backend,
        }

    jobs: list[dict[str, str]] = []
    pending = list(candidates)
    seen_scrape: set[str] = set()
    family_counts: dict[str, int] = defaultdict(int)
    max_per_family = _max_jobs_per_ats_family(SEARCH_SCRAPE_MAX)

    def _family_has_room(url: str) -> bool:
        return family_counts[_ats_family(url)] < max_per_family

    while pending and len(jobs) < SEARCH_SCRAPE_MAX:
        row = pending.pop(0)
        url = row["url"]
        if url in seen_scrape:
            continue
        seen_scrape.add(url)

        if not _family_has_room(url):
            continue

        # Skip hard hosts when we still have softer candidates waiting.
        if _is_hard_scrape_host(url) and any(
            not _is_hard_scrape_host(item["url"]) and _family_has_room(item["url"])
            for item in pending
        ):
            continue

        page, raw = _scrape_job_page(registry, visit_tool, url)
        if _is_blocked_page(page, raw):
            continue

        child_urls = [
            child
            for child in _posting_urls_from_page_text(raw, source_url=url)
            if _family_has_room(child)
        ]

        # Board listing page: follow a couple of child links instead of keeping the list URL.
        if _looks_like_board_listing_page(raw):
            for child in child_urls[:2]:
                if child not in seen_scrape:
                    pending.append({"title": "", "url": child, "snippet": ""})
            continue

        job = _job_row_from_page(page, raw, serp_title=row.get("title") or "")
        if job is None:
            for child in child_urls[:2]:
                if child not in seen_scrape:
                    pending.append({"title": "", "url": child, "snippet": ""})
            continue
        jobs.append(job)
        family_counts[_ats_family(url)] += 1

    message = ""
    if skipped:
        message = f"Omitted {skipped} invalid SERP row(s)."
    if not jobs:
        suffix = " No scraped pages yielded usable job postings."
        message = (message + suffix).strip()

    payload: JsonObject = {
        "jobs": jobs,
        "skipped": skipped,
        "message": message,
        "backend": backend,
    }
    registry.record_tool_output(json.dumps(payload))
    logger.info(
        "lg_search backend=%r query=%r jobs=%s skipped=%s",
        backend,
        query,
        len(jobs),
        skipped,
    )
    return payload


def search_queries_on_backend(
    queries: list[str],
    *,
    backend: str,
) -> tuple[list[FoundJob], list[str]]:
    """Run each query on one backend; return jobs + observed URL list."""
    registry = ToolObservedUrlRegistry()
    found: list[FoundJob] = []
    seen: set[str] = set()
    for query in queries:
        payload = search_job_postings(query, backend=backend, observed_urls=registry)
        jobs_raw = payload.get("jobs")
        if not isinstance(jobs_raw, list):
            continue
        for job in jobs_raw:
            job_dict = as_object_dict(job)
            if job_dict is None:
                continue
            url = str(job_dict.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            found.append(job_dict)
    return found, list(registry.urls)
