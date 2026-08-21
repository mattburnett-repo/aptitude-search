import pytest

from app.job_discovery.url_filters import (
    UrlFilters,
    _as_str_list,  # pyright: ignore[reportPrivateUsage]
    load_url_filters,
)


def test_as_str_list_rejects_empty_values():
    with pytest.raises(ValueError, match="non-empty strings"):
        _ = _as_str_list(["good", ""], field="skip_domains")


def test_as_str_list_allows_empty_when_requested():
    assert _as_str_list([], field="skip_domain_suffixes", allow_empty=True) == []


def test_load_url_filters_reads_configured_toml():
    load_url_filters.cache_clear()
    filters = load_url_filters()
    assert isinstance(filters, UrlFilters)
    assert "medium.com" in filters.skip_domains
    assert "example.com" in filters.skip_domains
    assert "suspended-domain.net" in filters.skip_domains
    assert filters.include_domains == frozenset()
    assert "totalh.net" in filters.skip_domain_suffixes
    assert "zya.me" in filters.skip_domain_suffixes
    assert filters.skip_title_phrases
    assert filters.closed_listing_phrases
    assert "no longer available" in filters.closed_listing_phrases
    assert "domain suspended" in filters.closed_listing_phrases
    assert filters.parking_gate_markers
    assert filters.error_page_markers
    assert filters.challenge_page_markers
