import json

from app.core.json_types import JsonObject
from app.core.models import Constraints
from app.job_discovery.discovery import run_job_discovery
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry


class _FakeSearchTool:
    _responses: list[str]
    call_count: int

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.call_count = 0

    def run_search_job_postings(self, query: str) -> str:
        _ = query
        response = self._responses[self.call_count]
        self.call_count += 1
        return response


def test_run_job_discovery_merges_and_dedupes_jobs(
    stage1_fixture: dict[str, object],
) -> None:
    registry = ToolObservedUrlRegistry()
    profile: JsonObject = stage1_fixture
    tool = _FakeSearchTool(
        [
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
    )

    from unittest.mock import patch

    with patch(
        "app.job_discovery.discovery.build_job_discovery_tools",
        return_value=[tool],
    ), patch(
        "app.job_discovery.discovery.build_discovery_queries",
        return_value=["senior Python jobs", "senior Django jobs"],
    ):
        found_jobs = run_job_discovery(
            profile,
            Constraints(),
            observed_urls=registry,
        )

    assert len(found_jobs) == 2
    assert tool.call_count == 2
