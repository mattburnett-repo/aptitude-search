#!/usr/bin/env python3
"""Precompute occupation-side embeddings for aptitude-to-jobtype matching.

This is a one-time (or re-run) database build step — not the UI/pipeline path.

Embedding has two sides, same model (config [embedding]):

  UI / pipeline (runtime, per request):
    resume (from UI) → Stage 1 aptitude profile → embed_aptitude_profile()
    in backend/app/core/embedding.py (BGE query instruction applied).

  Occupation corpus (this script, offline):
    O*NET tables → occupation_profile text (occupation_profile_from_onet.sql)
    → embed → store in occupation_embeddings.

At search time the pipeline embeds the aptitude profile once and compares it to
the precomputed vectors in occupation_embeddings (cosine similarity).

Prerequisites:
  - O*NET loaded (data/load-onet-postgres.sh)
  - backend/config.toml with [embedding] model_key + model + dimensions
  - pip install -r backend/requirements.txt (psycopg, huggingface_hub)

Run from repo root (or via data/load-onet-postgres.sh after O*NET load):
  python data/ingest/build_occupation_embeddings.py

Env: ONET_EMBED_BATCH_SIZE (default 16). Postgres: backend/config.toml [onet].
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import psycopg
from huggingface_hub import InferenceClient
from psycopg.abc import Query

REPO_ROOT = Path(__file__).resolve().parents[2]
INGEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import config  # noqa: E402
from app.core.embedding import embed_all_texts, vector_literal  # noqa: E402
from app.core.onet_db import connect  # noqa: E402

CREATE_TABLE_SCRIPT = INGEST_DIR / "create-occupation-embeddings-table.sh"
# SQL mashes O*NET rows into one occupation_profile text blob per SOC code.
OCCUPATION_PROFILE_SQL = INGEST_DIR / "occupation_profile_from_onet.sql"

BATCH_SIZE = max(1, int(os.environ.get("ONET_EMBED_BATCH_SIZE", "16")))
# BAAI/bge-large-en-v1.5 max context is 512 tokens; keep profiles conservative.
MAX_PROFILE_CHARS = 2000

INSERT_SQL = """
INSERT INTO occupation_embeddings (onetsoc_code, occupation_profile, embedding)
VALUES (%s, %s, %s::vector)
"""


def _ensure_table() -> None:
    if not CREATE_TABLE_SCRIPT.is_file():
        raise SystemExit(f"missing script: {CREATE_TABLE_SCRIPT}")
    _ = subprocess.run(
        [str(CREATE_TABLE_SCRIPT)],
        check=True,
    )


def _load_occupation_profile_sql() -> str:
    if not OCCUPATION_PROFILE_SQL.is_file():
        raise SystemExit(f"missing SQL: {OCCUPATION_PROFILE_SQL}")
    return OCCUPATION_PROFILE_SQL.read_text(encoding="utf-8")


def _fetch_profiles(conn: psycopg.Connection) -> list[tuple[str, str]]:
    """Load occupation_profile embedding payloads (text only; not from UI)."""
    query = cast(Query, _load_occupation_profile_sql())
    with conn.cursor() as cur:
        _ = cur.execute(query)
        rows = cast(list[tuple[str, str]], cur.fetchall())
    profiles: list[tuple[str, str]] = []
    for onetsoc_code, occupation_profile in rows:
        code = onetsoc_code.strip()
        profile = occupation_profile.strip()
        if len(profile) > MAX_PROFILE_CHARS:
            profile = profile[: MAX_PROFILE_CHARS - 3].rstrip() + "..."
        profiles.append((code, profile))
    return profiles


def _insert_rows(
    conn: psycopg.Connection,
    rows: list[tuple[str, str, list[float]]],
) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            INSERT_SQL,
            [(code, profile, vector_literal(vec)) for code, profile, vec in rows],
        )
    conn.commit()


def main() -> None:
    embedding = config.embedding
    onet = config.onet

    print(f"postgres: {onet.host}:{onet.port}/{onet.database}")
    print(f"model:    {embedding.model}")
    print(f"dims:     {embedding.dimensions}")
    print()

    _ensure_table()

    with connect() as conn:
        profiles = _fetch_profiles(conn)
        if not profiles:
            raise SystemExit("occupation profile query returned no occupations")

        print(f"occupations: {len(profiles)}")
        client = InferenceClient(api_key=embedding.model_key)
        # Passage side: no BGE query instruction (contrast embed_aptitude_profile).
        texts = [profile for _, profile in profiles]
        vectors = embed_all_texts(
            client,
            model=embedding.model,
            texts=texts,
            dimensions=embedding.dimensions,
            batch_size=BATCH_SIZE,
        )
        insert_rows = [
            (code, profile, vec)
            for (code, profile), vec in zip(profiles, vectors, strict=True)
        ]
        # occupation_profile = human-readable payload; embedding = vector for search.
        print("inserting rows...")
        _insert_rows(conn, insert_rows)

        with conn.cursor() as cur:
            _ = cur.execute("SELECT COUNT(*) FROM occupation_embeddings")
            count_row = cur.fetchone()
            if count_row is None:
                raise RuntimeError("COUNT(*) returned no row")
            count_value = cast(object, count_row[0])
            if isinstance(count_value, bool) or not isinstance(count_value, int):
                raise RuntimeError(f"unexpected COUNT(*) value: {count_value!r}")
            count = count_value

    print(f"done: {count} rows in occupation_embeddings")


if __name__ == "__main__":
    main()
