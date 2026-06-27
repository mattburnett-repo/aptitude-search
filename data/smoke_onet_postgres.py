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
FULL_ONET_TABLE_COUNT = 45
EMBED_ONLY_ONET_TABLE_COUNT = 7
OCCUPATION_EMBEDDINGS_TABLE = "occupation_embeddings"

EMBED_ONLY_TABLES = frozenset(
    {
        "content_model_reference",
        "scales_reference",
        "occupation_data",
        "abilities",
        "essential_skills",
        "transferable_skills",
        "job_titles",
    }
)

FULL_REQUIRED_TABLES = (
    "occupation_data",
    "content_model_reference",
    "abilities",
    "essential_skills",
    "transferable_skills",
    "work_activities",
    "job_titles",
    "related_occupations",
)

EMBED_ONLY_REQUIRED_TABLES = tuple(sorted(EMBED_ONLY_TABLES))

# Spot-check row counts (O*NET 30.3).
FULL_ROW_COUNTS: dict[str, int] = {
    "content_model_reference": 3006,
    "occupation_data": EXPECTED_OCCUPATION_COUNT,
    "abilities": 92976,
    "essential_skills": 17880,
    "transferable_skills": 44700,
    "work_activities": 73308,
    "job_titles": 57543,
    "related_occupations": 18460,
    "gwas_to_iwas": 332,
    "gwas_to_iwas_to_dwas": 2087,
}

EMBED_ONLY_ROW_COUNTS: dict[str, int] = {
    key: FULL_ROW_COUNTS[key]
    for key in EMBED_ONLY_TABLES
}


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


def _public_tables() -> set[str]:
    return set(
        _run_psql_tuples(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';",
        )
    )


def _load_mode(public_tables: set[str]) -> str:
    onet_tables = public_tables - {OCCUPATION_EMBEDDINGS_TABLE}
    if onet_tables == EMBED_ONLY_TABLES:
        return "embed-only"
    if len(onet_tables) == FULL_ONET_TABLE_COUNT:
        return "full"
    return "unknown"


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


def check_vector_extension() -> CheckResult:
    rows = _run_psql_tuples(
        "SELECT 1 FROM pg_extension WHERE extname = 'vector';",
    )
    if rows == ["1"]:
        return CheckResult("pgvector extension", True, "vector")
    return CheckResult(
        "pgvector extension",
        False,
        "CREATE EXTENSION vector; required for occupation_embeddings",
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


def check_public_table_count(*, public_tables: set[str], load_mode: str) -> CheckResult:
    if load_mode == "unknown":
        return CheckResult(
            "public table count",
            False,
            f"unrecognized layout ({len(public_tables)} tables); expected full ({FULL_ONET_TABLE_COUNT}) "
            f"or embed-only ({EMBED_ONLY_ONET_TABLE_COUNT}) O*NET load",
        )

    has_embed_table = OCCUPATION_EMBEDDINGS_TABLE in public_tables
    expected_onet = (
        EMBED_ONLY_ONET_TABLE_COUNT if load_mode == "embed-only" else FULL_ONET_TABLE_COUNT
    )
    expected = expected_onet + (1 if has_embed_table else 0)
    count = len(public_tables)
    if count != expected:
        return CheckResult(
            "public table count",
            False,
            f"got {count}, expected {expected} ({load_mode}"
            + (" + occupation_embeddings)" if has_embed_table else ")"),
        )
    suffix = " + occupation_embeddings" if has_embed_table else ""
    return CheckResult(
        "public table count",
        True,
        f"{count} ({load_mode}{suffix})",
    )


def check_required_tables_present(*, public_tables: set[str], load_mode: str) -> CheckResult:
    required = (
        EMBED_ONLY_REQUIRED_TABLES
        if load_mode == "embed-only"
        else FULL_REQUIRED_TABLES
    )
    missing = [t for t in required if t not in public_tables]
    if missing:
        return CheckResult(
            "required O*NET tables",
            False,
            f"missing: {', '.join(missing)}",
        )
    return CheckResult(
        "required O*NET tables",
        True,
        ", ".join(required),
    )


def check_occupation_embeddings(*, public_tables: set[str]) -> CheckResult:
    if OCCUPATION_EMBEDDINGS_TABLE not in public_tables:
        return CheckResult(
            "occupation_embeddings",
            True,
            "not present (O*NET-only load; run create-occupation-embeddings-table.sh)",
        )

    rows = _run_psql_tuples(
        f"SELECT COUNT(*) FROM {OCCUPATION_EMBEDDINGS_TABLE};",
    )
    if len(rows) != 1 or not rows[0].isdigit():
        return CheckResult("occupation_embeddings count", False, f"unexpected output: {rows!r}")
    count = int(rows[0])
    if count == EXPECTED_OCCUPATION_COUNT:
        return CheckResult("occupation_embeddings count", True, str(count))
    if count == 0:
        return CheckResult(
            "occupation_embeddings count",
            True,
            "0 (empty — run data/embed/build_occupation_embeddings.py or ONET_SKIP_EMBED=1)",
        )
    return CheckResult(
        "occupation_embeddings count",
        False,
        f"got {count}, expected {EXPECTED_OCCUPATION_COUNT} or 0",
    )


def check_row_counts(*, load_mode: str) -> list[CheckResult]:
    if load_mode == "unknown":
        return []

    row_counts = EMBED_ONLY_ROW_COUNTS if load_mode == "embed-only" else FULL_ROW_COUNTS
    results: list[CheckResult] = []
    for table, expected in row_counts.items():
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

        public_tables = _public_tables()
        load_mode = _load_mode(public_tables)
        has_embed_table = OCCUPATION_EMBEDDINGS_TABLE in public_tables

        checks.extend(
            [
                check_connection(),
                check_database_exists(),
                check_occupation_count(),
                check_public_table_count(public_tables=public_tables, load_mode=load_mode),
                check_required_tables_present(
                    public_tables=public_tables,
                    load_mode=load_mode,
                ),
                check_software_developers_sample(),
            ]
        )
        if has_embed_table:
            checks.append(check_vector_extension())
        checks.append(check_occupation_embeddings(public_tables=public_tables))
        if load_mode != "unknown":
            checks.extend(check_row_counts(load_mode=load_mode))
    except RuntimeError as exc:
        checks.append(CheckResult("runtime", False, str(exc)))
        return _report(checks, load_mode="unknown")

    exit_code = _report(checks, load_mode=load_mode)
    if all(c.ok for c in checks):
        print_dt_listing()
    return exit_code


def _report(checks: Sequence[CheckResult], *, load_mode: str | None = None) -> int:
    mode_label = f" — {load_mode}" if load_mode and load_mode != "unknown" else ""
    print(f"O*NET Postgres smoke test{mode_label} — {config.onet.host}/{EXPECTED_DATABASE}\n")
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
