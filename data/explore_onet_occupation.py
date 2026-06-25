#!/usr/bin/env python3
"""Explore O*NET occupation data in Postgres (sample: Software Developers).

Run from repo root:
  python data/explore_onet_occupation.py
  ONET_EXPLORE_SOC=15-1252.00 python data/explore_onet_occupation.py

Env: ONET_PGDATABASE (default onet_30_3_local_full), PGHOST, PGPORT, PGUSER, etc.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

DATABASE = os.environ.get("ONET_PGDATABASE", "onet_30_3_local_full")
SOC_CODE = os.environ.get("ONET_EXPLORE_SOC", "15-1252.00")


def _run_query(title: str, sql: str) -> None:
    if shutil.which("psql") is None:
        raise RuntimeError("psql not found on PATH")

    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}\n")

    result = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1", "-d", DATABASE, "-c", sql],
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> None:
    soc = SOC_CODE.replace("'", "''")

    _run_query(
        "Occupation count",
        "SELECT COUNT(*) FROM occupation_data;",
    )

    _run_query(
        f"Occupation record ({SOC_CODE})",
        f"SELECT * FROM occupation_data WHERE onetsoc_code = '{soc}';",
    )

    _run_query(
        f"Top work activities by importance — element_id ({SOC_CODE})",
        f"""
        SELECT element_id, data_value
        FROM work_activities
        WHERE onetsoc_code = '{soc}' AND scale_id = 'IM'
        ORDER BY data_value DESC
        LIMIT 10;
        """.strip(),
    )

    _run_query(
        f"Top work activities by importance — names ({SOC_CODE})",
        f"""
        SELECT wa.data_value, cmr.element_name, cmr.description
        FROM work_activities wa
        JOIN content_model_reference cmr ON cmr.element_id = wa.element_id
        WHERE wa.onetsoc_code = '{soc}' AND wa.scale_id = 'IM'
        ORDER BY wa.data_value DESC
        LIMIT 10;
        """.strip(),
    )

    _run_query(
        f"Alternate job titles ({SOC_CODE})",
        f"""
        SELECT job_title FROM job_titles
        WHERE onetsoc_code = '{soc}'
        LIMIT 20;
        """.strip(),
    )

    _run_query(
        f"Related occupations ({SOC_CODE})",
        f"""
        SELECT ro.related_onetsoc_code, od.title
        FROM related_occupations ro
        JOIN occupation_data od ON od.onetsoc_code = ro.related_onetsoc_code
        WHERE ro.onetsoc_code = '{soc}'
        ORDER BY ro.related_index
        LIMIT 10;
        """.strip(),
    )


if __name__ == "__main__":
    print(f"database: {DATABASE}")
    print(f"soc code: {SOC_CODE}")
    main()
