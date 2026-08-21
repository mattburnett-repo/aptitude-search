from unittest.mock import MagicMock, patch

import httpx

from app.job_discovery.listing_gate import (
    _exa_exclude_text,
    accept_serp_row,
    filter_serp_rows,
    url_looks_live,
)


def test_exa_exclude_text_one_phrase_max_five_words() -> None:
    assert _exa_exclude_text(()) is None
    assert _exa_exclude_text(("this job is no longer open", "six words is too many here")) is None
    assert _exa_exclude_text(
        (
            "this job is no longer open",
            "no longer available",
            "no longer open",
        )
    ) == ["no longer available"]


def test_url_looks_live_true_when_check_disabled() -> None:
    with patch(
        "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
        False,
    ):
        assert url_looks_live("https://acme.com/jobs/1") is True


def test_url_looks_live_false_on_404() -> None:
    response = MagicMock()
    response.status_code = 404
    response.content = b""
    response.url = "https://acme.com/jobs/1"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
    ):
        assert url_looks_live("https://acme.com/jobs/1") is False


def test_url_looks_live_false_on_closed_phrase() -> None:
    response = MagicMock()
    response.status_code = 200
    response.content = b"Sorry, this job is no longer available."
    response.url = "https://acme.com/jobs/1"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
        patch(
            "app.job_discovery.listing_gate.load_url_filters",
            return_value=MagicMock(
                closed_listing_phrases=("no longer available",),
                parking_gate_markers=(),
                error_page_markers=(),
                challenge_page_markers=(),
            ),
        ),
    ):
        assert url_looks_live("https://acme.com/jobs/1") is False


def test_url_looks_live_true_on_network_error() -> None:
    client = MagicMock()
    client.get.side_effect = httpx.ConnectError("timed out")
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
        patch("app.job_discovery.listing_gate._exa_fetch_text", return_value=None),
    ):
        assert url_looks_live("https://acme.com/jobs/1") is True


def test_url_looks_live_true_on_healthy_page() -> None:
    response = MagicMock()
    response.status_code = 200
    response.content = b"We are hiring a Backend Engineer."
    response.url = "https://acme.com/jobs/1"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
        patch(
            "app.job_discovery.listing_gate.load_url_filters",
            return_value=MagicMock(
                closed_listing_phrases=("no longer available",),
                parking_gate_markers=(),
                error_page_markers=(),
                challenge_page_markers=(),
            ),
        ),
    ):
        assert url_looks_live("https://acme.com/jobs/1") is True


def test_url_looks_live_false_on_410() -> None:
    response = MagicMock()
    response.status_code = 410
    response.content = b""
    response.url = "https://acme.com/jobs/1"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
    ):
        assert url_looks_live("https://acme.com/jobs/1") is False


def test_url_looks_live_false_on_junk_final_url() -> None:
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
    ):
        assert url_looks_live("https://taskworks.totalh.net/jobs/1") is False


def test_url_looks_live_false_on_parking_gate() -> None:
    response = MagicMock()
    response.status_code = 200
    response.content = (
        b'<html><body><script type="text/javascript" src="/aes.js"></script>'
        b"<script>function toNumbers(d){return d}</script></body></html>"
    )
    response.url = "https://example-jobs.test/jobs/1"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
        patch(
            "app.job_discovery.listing_gate.should_skip_search_result",
            return_value=False,
        ),
        patch(
            "app.job_discovery.listing_gate.load_url_filters",
            return_value=MagicMock(
                closed_listing_phrases=(),
                parking_gate_markers=('src="/aes.js"',),
                error_page_markers=(),
                challenge_page_markers=(),
            ),
        ),
    ):
        assert url_looks_live("https://example-jobs.test/jobs/1") is False


def test_url_looks_live_false_on_suspended_domain_url() -> None:
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
    ):
        assert (
            url_looks_live(
                "https://suspended-domain.net/index.php?host=flexgen.zya.me"
            )
            is False
        )


def test_url_looks_live_false_on_500_aspnet_error() -> None:
    response = MagicMock()
    response.status_code = 500
    response.content = (
        b"<title>Object reference not set to an instance of an object.</title>"
    )
    response.url = (
        "https://careers.globelifeinsurance.com/jobs/job-details/"
        "customer-care-job-jr101280?jobid=JR101280"
    )
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
    ):
        assert (
            url_looks_live(
                "https://careers.globelifeinsurance.com/jobs/job-details/"
                "customer-care-job-jr101280?searchSource=c&jobid=JR101280"
            )
            is False
        )


def test_url_looks_live_uses_exa_when_cloudflare_blocks() -> None:
    response = MagicMock()
    response.status_code = 403
    response.content = b"<title>Just a moment...</title> cloudflare"
    response.url = "https://jobs.sitepoint.com/adaptive-teams/job-1/"
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    with (
        patch(
            "app.job_discovery.listing_gate.config.job_discovery.url_liveness_check",
            True,
        ),
        patch("app.job_discovery.listing_gate.httpx.Client", return_value=client),
        patch(
            "app.job_discovery.listing_gate._exa_fetch_text",
            return_value="Sorry, looks like this job is no longer open",
        ),
        patch(
            "app.job_discovery.listing_gate.load_url_filters",
            return_value=MagicMock(
                closed_listing_phrases=("no longer open",),
                parking_gate_markers=(),
                error_page_markers=(),
                challenge_page_markers=("just a moment", "cloudflare"),
            ),
        ),
    ):
        assert (
            url_looks_live(
                "https://jobs.sitepoint.com/adaptive-teams/"
                "customer-service-representative-7855254/"
            )
            is False
        )


def test_accept_serp_row_and_filter_rows() -> None:
    with patch("app.job_discovery.listing_gate.url_looks_live", return_value=True):
        job = accept_serp_row(
            title="Backend Engineer",
            url="https://acme.com/careers/backend",
            content="hiring for Django",
        )
        assert job is not None
        assert job["url"] == "https://acme.com/careers/backend"

        rejected = accept_serp_row(
            title="How to learn Python",
            url="https://medium.com/some-article",
            content="blog",
        )
        assert rejected is None

        jobs = filter_serp_rows(
            [
                {
                    "title": "Backend Engineer",
                    "url": "https://acme.com/careers/backend",
                    "content": "hiring",
                },
                {
                    "title": "Gone",
                    "url": "https://suspended-domain.net/index.php?host=x",
                    "content": "x",
                },
            ]
        )
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Backend Engineer"
