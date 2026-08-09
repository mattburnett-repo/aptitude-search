from unittest.mock import patch

from app.core.json_types import JsonObject
from app.core.models import Constraints
from app.job_discovery.discovery import run_job_discovery


def test_run_job_discovery_merges_and_dedupes_jobs(
    stage1_fixture: dict[str, object],
) -> None:
    profile: JsonObject = stage1_fixture
    responses = [
        [
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://acme.com/careers/backend",
                "location": "Remote",
            }
        ],
        [
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://acme.com/careers/backend",
                "location": "Remote",
            },
            {
                "title": "Python Developer",
                "company": "Beta",
                "url": "https://beta.com/jobs/python",
                "location": "Toronto",
            },
        ],
    ]

    with patch(
        "app.job_discovery.discovery.search_job_postings",
        side_effect=responses,
    ) as mock_search, patch(
        "app.job_discovery.discovery.build_discovery_queries",
        return_value=["senior Python jobs", "senior Django jobs"],
    ):
        found_jobs = run_job_discovery(profile, Constraints())

    assert len(found_jobs) == 2
    assert mock_search.call_count == 2
