import json
from unittest.mock import MagicMock, patch

from app.core.models import Constraints
from app.job_discovery.planned_discovery import run_planned_job_discovery
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry


def test_run_planned_job_discovery_merges_and_dedupes_jobs(
    stage1_fixture: dict[str, object],
) -> None:
    registry = ToolObservedUrlRegistry()
    tool = MagicMock()
    tool.run_search_job_postings.side_effect = [
        json.dumps(
            {
                "jobs": [
                    {
                        "title": "Backend Engineer",
                        "company": "Acme",
                        "url": "https://acme.com/careers/backend",
                        "location": "Remote",
                    }
                ],
                "skipped": 0,
                "message": "",
            }
        ),
        json.dumps(
            {
                "jobs": [
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
                "skipped": 0,
                "message": "",
            }
        ),
    ]

    with patch(
        "app.job_discovery.planned_discovery.build_job_discovery_tools",
        return_value=[tool],
    ), patch(
        "app.job_discovery.planned_discovery.build_discovery_queries",
        return_value=["senior Python jobs", "senior Django jobs"],
    ):
        found_jobs = run_planned_job_discovery(
            stage1_fixture,
            Constraints(),
            observed_urls=registry,
        )

    assert len(found_jobs) == 2
    assert tool.run_search_job_postings.call_count == 2
