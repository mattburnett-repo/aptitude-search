"""Spike/notebook helpers for ATS and careers URL heuristics."""

from __future__ import annotations

from app.job_discovery.url_utils import normalize_result_url

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


def looks_like_job_posting_url(url: str) -> bool:
    """True when URL path/host resembles a careers page or ATS posting."""
    prepared, error = normalize_result_url(url)
    if error or not prepared:
        return False
    lower = prepared.lower()
    return any(marker in lower for marker in _JOB_URL_MARKERS)
