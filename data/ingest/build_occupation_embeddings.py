#!/usr/bin/env python3
"""Build occupation_embeddings: O*NET occupation profiles → embed → insert.

Prerequisites:
  - O*NET loaded (data/load-onet-postgres.sh)
  - backend/config.toml with [embedding] model_key + model + dimensions
  - pip install -r backend/requirements.txt (psycopg, huggingface_hub)

Run from repo root (or via data/load-onet-postgres.sh after O*NET load):
  python data/ingest/build_occupation_embeddings.py

Env: ONET_EMBED_BATCH_SIZE (default 16). Postgres: backend/config.toml [onet].
"""

from __future__ import annotations

import math
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
from app.core.onet_db import connect  # noqa: E402

CREATE_TABLE_SCRIPT = INGEST_DIR / "create-occupation-embeddings-table.sh"
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


def _as_float_list(value: object) -> list[float] | None:
    if not isinstance(value, list):
        return None
    out: list[float] = []
    for item in cast(list[object], value):
        if not isinstance(item, (int, float)):
            return None
        out.append(float(item))
    return out


def _as_float_matrix(value: object) -> list[list[float]] | None:
    if not isinstance(value, list):
        return None
    rows: list[list[float]] = []
    for item in cast(list[object], value):
        row = _as_float_list(item)
        if row is None:
            return None
        rows.append(row)
    return rows


def _mean_pool_rows(rows: list[list[float]], *, expected_dim: int) -> list[float]:
    return [sum(row[i] for row in rows) / len(rows) for i in range(expected_dim)]


def _flatten_embedding(raw: object, *, expected_dim: int) -> list[float]:
    flat = _as_float_list(raw)
    if flat is not None:
        vector = flat
    else:
        matrix = _as_float_matrix(raw)
        if matrix is None or not matrix:
            raise ValueError("empty embedding response")
        if len(matrix) == 1 and len(matrix[0]) == expected_dim:
            vector = matrix[0]
        elif all(len(row) == expected_dim for row in matrix):
            vector = _mean_pool_rows(matrix, expected_dim=expected_dim)
        else:
            raise ValueError("unexpected nested embedding shape")

    if len(vector) != expected_dim:
        raise ValueError(
            f"unexpected embedding length {len(vector)}, expected {expected_dim}"
        )
    return vector


def _parse_embeddings(
    raw: object,
    *,
    expected_dim: int,
    expected_count: int,
) -> list[list[float]]:
    if expected_count == 1:
        return [_flatten_embedding(raw, expected_dim=expected_dim)]

    matrix = _as_float_matrix(raw)
    if matrix is not None and len(matrix) == expected_count:
        return [_flatten_embedding(item, expected_dim=expected_dim) for item in matrix]

    length: int | str = len(cast(list[object], raw)) if isinstance(raw, list) else "n/a"
    raise ValueError(f"batch embedding response length {length} != {expected_count}")


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


def _embed_batch(
    client: InferenceClient,
    *,
    model: str,
    texts: list[str],
    dimensions: int,
) -> list[list[float]]:
    raw = cast(
        object,
        client.feature_extraction(texts, model=model),  # pyright: ignore[reportUnknownMemberType]
    )
    vectors = _parse_embeddings(raw, expected_dim=dimensions, expected_count=len(texts))
    return [_normalize(vector) for vector in vectors]


def _embed_all(
    client: InferenceClient,
    *,
    model: str,
    texts: list[str],
    dimensions: int,
    batch_size: int,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    total = len(texts)
    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        end = min(start + batch_size, total)
        print(f"embedding {start + 1}-{end} / {total}...")
        try:
            batch_vectors = _embed_batch(
                client, model=model, texts=batch, dimensions=dimensions
            )
        except Exception:
            if len(batch) == 1:
                raise
            # Some HF backends reject batch input; fall back to one text at a time.
            batch_vectors: list[list[float]] = []
            for text in batch:
                batch_vectors.extend(
                    _embed_batch(client, model=model, texts=[text], dimensions=dimensions)
                )
        if len(batch_vectors) != len(batch):
            raise ValueError(
                f"embedding count mismatch: got {len(batch_vectors)} for batch of {len(batch)}"
            )
        vectors.extend(batch_vectors)
    return vectors


def _insert_rows(
    conn: psycopg.Connection,
    rows: list[tuple[str, str, list[float]]],
) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            INSERT_SQL,
            [(code, profile, _vector_literal(vec)) for code, profile, vec in rows],
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
        texts = [profile for _, profile in profiles]
        vectors = _embed_all(
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
