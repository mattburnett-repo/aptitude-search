#!/usr/bin/env python3
"""Smoke-test Stage 2 planned discovery (profile-driven queries). Run from backend/."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.models import Constraints
from app.job_discovery.planned_discovery import (
    build_discovery_queries,
    run_planned_job_discovery,
)


def main() -> None:
    fixture_path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "example-outputs"
        / "career-changer-mixed-stack-stage1.json"
    )
    profile = json.loads(fixture_path.read_text(encoding="utf-8"))
    constraints = Constraints(location="Toronto, ON", remote_preference="remote")

    queries = build_discovery_queries(profile, constraints)
    print("--- planned queries ---")
    for query in queries:
        print(query)

    found_jobs = run_planned_job_discovery(profile, constraints)
    print("--- found_jobs ---")
    print(json.dumps(found_jobs[:5], indent=2))


if __name__ == "__main__":
    main()
