"""Load job-discovery URL filter lists from external TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

from app.core.config import config

_JOB_DISCOVERY_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class UrlFilters:
    skip_domains: frozenset[str]
    skip_domain_suffixes: tuple[str, ...]
    skip_path_markers: tuple[str, ...]
    skip_listing_path_markers: tuple[str, ...]
    skip_listing_path_markers_case_sensitive: tuple[str, ...]
    skip_title_phrases: tuple[str, ...]
    job_url_markers: tuple[str, ...]


def _as_str_list(raw: object, *, field: str) -> list[str]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{field} must be a non-empty array of strings")
    values: list[str] = []
    for item in cast(list[object], raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain only non-empty strings")
        values.append(item.strip())
    return values


@lru_cache
def load_url_filters() -> UrlFilters:
    path = _JOB_DISCOVERY_DIR / config.job_discovery.url_filters_file
    with path.open("rb") as f:
        data = tomllib.load(f)
    return UrlFilters(
        skip_domains=frozenset(_as_str_list(data.get("skip_domains"), field="skip_domains")),
        skip_domain_suffixes=tuple(
            _as_str_list(
                data.get("skip_domain_suffixes"),
                field="skip_domain_suffixes",
            )
        ),
        skip_path_markers=tuple(
            _as_str_list(data.get("skip_path_markers"), field="skip_path_markers")
        ),
        skip_listing_path_markers=tuple(
            _as_str_list(
                data.get("skip_listing_path_markers"),
                field="skip_listing_path_markers",
            )
        ),
        skip_listing_path_markers_case_sensitive=tuple(
            _as_str_list(
                data.get("skip_listing_path_markers_case_sensitive"),
                field="skip_listing_path_markers_case_sensitive",
            )
        ),
        skip_title_phrases=tuple(
            _as_str_list(data.get("skip_title_phrases"), field="skip_title_phrases")
        ),
        job_url_markers=tuple(
            _as_str_list(data.get("job_url_markers"), field="job_url_markers")
        ),
    )
