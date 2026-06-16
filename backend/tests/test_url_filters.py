import pytest

from app.job_discovery.url_filters import (
    UrlFilters,
    _as_str_list,  # pyright: ignore[reportPrivateUsage]
    load_url_filters,
)


def test_as_str_list_rejects_empty_values():
    with pytest.raises(ValueError, match="non-empty strings"):
        _ = _as_str_list(["good", ""], field="skip_domains")


def test_load_url_filters_reads_configured_toml():
    filters = load_url_filters()
    assert isinstance(filters, UrlFilters)
    assert "medium.com" in filters.skip_domains
    assert "example.com" in filters.skip_domains
    assert filters.job_url_markers
