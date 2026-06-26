#!/usr/bin/env python3
"""Smoke-test O*NET 30.3 Postgres load (after data/load-onet-postgres.sh).

Run from repo root:
  python data/smoke_onet_postgres.py

Env: backend/config.toml [onet] for Postgres connection.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import config  # noqa: E402

ONET_CONNINFO = config.onet.conninfo()
EXPECTED_DATABASE = config.onet.database

EXPECTED_OCCUPATION_COUNT = 1016
EXPECTED_TABLE_COUNT = 45

# Spot-check row counts for large / aptitude-to-jobtype matching tables (O*NET 30.3).
EXPECTED_ROW_COUNTS: dict[str, int] = {
    "content_model_reference": 3006,
    "occupation_data": EXPECTED_OCCUPATION_COUNT,
    "work_activities": 73308,
    "job_titles": 57543,
    "related_occupations": 18460,
    "gwas_to_iwas": 332,
    "gwas_to_iwas_to_dwas": 2087,
}

APTITUDE_TO_JOBTYPE_MATCHING_TABLES = (
    "occupation_data",
    "content_model_reference",
    "work_activities",
    "job_titles",
    "related_occupations",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _psql_base_args() -> list[str]:
    if shutil.which("psql") is None:
        raise RuntimeError("psql not found on PATH")
    return ["psql", "-v", "ON_ERROR_STOP=1"]


def _run_psql(
    sql: str,
    *,
    conninfo: str = ONET_CONNINFO,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = [*_psql_base_args(), "-d", conninfo, "-c", sql]
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=capture,
    )


def _run_psql_tuples(sql: str, *, conninfo: str = ONET_CONNINFO) -> list[str]:
    cmd = [*_psql_base_args(), "-d", conninfo, "-t", "-A", "-c", sql]
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"psql failed: {sql[:80]}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_psql_available() -> CheckResult:
    path = shutil.which("psql")
    if path is None:
        return CheckResult("psql on PATH", False, "not found")
    return CheckResult("psql on PATH", True, path)


def check_database_exists() -> CheckResult:
    rows = _run_psql_tuples("SELECT current_database();")
    if rows == [EXPECTED_DATABASE]:
        return CheckResult("database", True, EXPECTED_DATABASE)
    return CheckResult(
        "database",
        False,
        f"connected as {rows!r}, expected {EXPECTED_DATABASE!r}",
    )


def check_connection() -> CheckResult:
    result = _run_psql("SELECT 1 AS ok;")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "connection failed").strip()
        return CheckResult("connection", False, detail)
    return CheckResult(
        "connection",
        True,
        f"{config.onet.host}:{config.onet.port}/{EXPECTED_DATABASE}",
    )


def check_occupation_count() -> CheckResult:
    rows = _run_psql_tuples(
        "SELECT COUNT(*) FROM occupation_data;",
    )
    if len(rows) != 1 or not rows[0].isdigit():
        return CheckResult("occupation_data count", False, f"unexpected output: {rows!r}")
    count = int(rows[0])
    if count != EXPECTED_OCCUPATION_COUNT:
        return CheckResult(
            "occupation_data count",
            False,
            f"got {count}, expected {EXPECTED_OCCUPATION_COUNT}",
        )
    return CheckResult(
        "occupation_data count",
        True,
        str(count),
    )


def check_public_table_count() -> CheckResult:
    rows = _run_psql_tuples(
        "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';",
    )
    count = int(rows[0])
    if count != EXPECTED_TABLE_COUNT:
        return CheckResult(
            "public table count",
            False,
            f"got {count}, expected {EXPECTED_TABLE_COUNT}",
        )
    return CheckResult("public table count", True, str(count))


def check_row_counts() -> list[CheckResult]:
    results: list[CheckResult] = []
    for table, expected in EXPECTED_ROW_COUNTS.items():
        rows = _run_psql_tuples(
            f"SELECT COUNT(*) FROM {table};",
        )
        count = int(rows[0])
        ok = count == expected
        results.append(
            CheckResult(
                f"{table} rows",
                ok,
                f"{count}" if ok else f"got {count}, expected {expected}",
            )
        )
    return results


def check_aptitude_to_jobtype_matching_tables_present() -> CheckResult:
    names = set(
        _run_psql_tuples(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';",
        )
    )
    missing = [t for t in APTITUDE_TO_JOBTYPE_MATCHING_TABLES if t not in names]
    if missing:
        return CheckResult(
            "aptitude-to-jobtype matching tables",
            False,
            f"missing: {', '.join(missing)}",
        )
    return CheckResult(
        "aptitude-to-jobtype matching tables",
        True,
        ", ".join(APTITUDE_TO_JOBTYPE_MATCHING_TABLES),
    )


def check_software_developers_sample() -> CheckResult:
    rows = _run_psql_tuples(
        """
        SELECT title
        FROM occupation_data
        WHERE onetsoc_code = '15-1252.00';
        """,
    )
    if rows != ["Software Developers"]:
        return CheckResult(
            "Software Developers row",
            False,
            f"unexpected: {rows!r}",
        )
    return CheckResult("Software Developers row", True, rows[0])


def print_dt_listing() -> None:
    print("\n--- public tables (psql \\dt equivalent) ---")
    result = _run_psql(
        r"\dt public.*",
        capture=True,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout or "\\dt failed")
        return
    print(result.stdout.rstrip())


def run_checks() -> int:
    checks: list[CheckResult] = []

    try:
        checks.append(check_psql_available())
        if not checks[-1].ok:
            return _report(checks)

        checks.extend(
            [
                check_connection(),
                check_database_exists(),
                check_occupation_count(),
                check_public_table_count(),
                check_aptitude_to_jobtype_matching_tables_present(),
                check_software_developers_sample(),
            ]
        )
        checks.extend(check_row_counts())
    except RuntimeError as exc:
        checks.append(CheckResult("runtime", False, str(exc)))
        return _report(checks)

    exit_code = _report(checks)
    if all(c.ok for c in checks):
        print_dt_listing()
    return exit_code


def _report(checks: Sequence[CheckResult]) -> int:
    print(f"O*NET Postgres smoke test — {config.onet.host}/{EXPECTED_DATABASE}\n")
    failed = 0
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"  [{status}] {check.name}: {check.detail}")
        if not check.ok:
            failed += 1
    print()
    if failed:
        print(f"{failed} check(s) failed.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_checks())
