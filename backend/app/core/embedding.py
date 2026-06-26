"""Shared Hugging Face embedding helpers (BGE) for aptitude-to-jobtype matching.

This module is not UI-only. It holds:

  Shared (both paths):
    flatten_embedding, normalize_embedding, embed_texts, vector_literal, …

  Offline occupation corpus (called from data/ingest/build_occupation_embeddings.py):
    embed_all_texts — O*NET occupation_profile text, no BGE query prefix.

  UI / pipeline runtime (called from pipeline after Stage 1):
    aptitude_text_for_embedding, embed_aptitude_profile — Stage 1 aptitude
    profile from resume; BGE_QUERY_INSTRUCTION prepended.

Same model (config [embedding]) for both paths. At search time embed_aptitude_profile
compares against precomputed occupation_embeddings rows in Postgres.
"""

from __future__ import annotations

import math
from typing import cast

from huggingface_hub import InferenceClient
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import JsonObject
from app.core.profile_text import labeled_names


# --- Shared: HF response parsing and feature_extraction wrappers ---


def _embedding_client() -> InferenceClient:
    return InferenceClient(api_key=config.embedding.model_key)


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


def flatten_embedding(raw: object, *, expected_dim: int) -> list[float]:
    """Normalize HF feature_extraction response shapes to a single vector."""
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
        return [flatten_embedding(raw, expected_dim=expected_dim)]

    matrix = _as_float_matrix(raw)
    if matrix is not None and len(matrix) == expected_count:
        return [flatten_embedding(item, expected_dim=expected_dim) for item in matrix]

    length: int | str = len(cast(list[object], raw)) if isinstance(raw, list) else "n/a"
    raise ValueError(f"batch embedding response length {length} != {expected_count}")


def normalize_embedding(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def vector_literal(vector: list[float]) -> str:
    """Postgres pgvector literal for occupation_embeddings inserts."""
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


def embed_texts(
    client: InferenceClient,
    *,
    model: str,
    texts: list[str],
    dimensions: int,
) -> list[list[float]]:
    """Call HF feature_extraction; used by both ingest and embed_aptitude_profile."""
    raw = cast(
        object,
        client.feature_extraction(texts, model=model),  # pyright: ignore[reportUnknownMemberType]
    )
    vectors = _parse_embeddings(raw, expected_dim=dimensions, expected_count=len(texts))
    return [normalize_embedding(vector) for vector in vectors]


# --- Offline: occupation corpus ingest (not UI) ---


def embed_all_texts(
    client: InferenceClient,
    *,
    model: str,
    texts: list[str],
    dimensions: int,
    batch_size: int,
) -> list[list[float]]:
    """Batch embed passage texts (occupation corpus ingest; no BGE query prefix)."""
    vectors: list[list[float]] = []
    total = len(texts)
    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        end = min(start + batch_size, total)
        print(f"embedding {start + 1}-{end} / {total}...")
        try:
            batch_vectors = embed_texts(
                client, model=model, texts=batch, dimensions=dimensions
            )
        except Exception:
            if len(batch) == 1:
                raise
            batch_vectors = [
                embed_texts(client, model=model, texts=[text], dimensions=dimensions)[0]
                for text in batch
            ]
        if len(batch_vectors) != len(batch):
            raise ValueError(
                f"embedding count mismatch: got {len(batch_vectors)} for batch of {len(batch)}"
            )
        vectors.extend(batch_vectors)
    return vectors


# --- UI / pipeline: aptitude profile from resume → Stage 1 ---

# BGE v1.5: query instruction for aptitude text only (not used by embed_all_texts).
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def aptitude_text_for_embedding(profile: JsonObject) -> str:
    """Build aptitude embedding payload from Stage 1 output (work-pattern fields only)."""
    summary_raw = profile.get("aptitude_summary")
    summary = summary_raw.strip() if isinstance(summary_raw, str) else ""

    parts: list[str] = []
    if summary:
        parts.append(f"Summary: {summary}")

    strengths = labeled_names(profile.get("strengths"), limit=6)
    if strengths:
        parts.append(f"Strengths: {strengths}")

    work_style = labeled_names(profile.get("working_style_signals"), limit=6)
    if work_style:
        parts.append(f"Work style: {work_style}")

    if not parts:
        raise ValueError("aptitude profile has no embeddable text")
    return "\n".join(parts)


@traceable(run_type="embedding", name="aptitude_profile")
def embed_aptitude_profile(profile: JsonObject) -> list[float]:
    """Embed Stage 1 aptitude profile at pipeline runtime (UI → resume → Stage 1)."""
    text = BGE_QUERY_INSTRUCTION + aptitude_text_for_embedding(profile)
    vectors = embed_texts(
        _embedding_client(),
        model=config.embedding.model,
        texts=[text],
        dimensions=config.embedding.dimensions,
    )
    return vectors[0]
