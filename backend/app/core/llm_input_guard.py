"""Prompt Guard classification for resume injection screening."""

from __future__ import annotations

import logging
from functools import lru_cache

from huggingface_hub import InferenceClient
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config

logger = logging.getLogger(__name__)


def _chunk_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    return [text[start : start + max_chars] for start in range(0, len(text), max_chars)]


def _is_malicious_label(label: str) -> bool:
    normalized = label.strip().lower().replace("_", " ")
    if "malicious" in normalized:
        return True
    if normalized in {"label 1", "1"}:
        return True
    return normalized.endswith("1") and "benign" not in normalized


@lru_cache(maxsize=1)
def _input_guard_client() -> InferenceClient:
    return InferenceClient(api_key=config.llm.input_guard.model_key)


@traceable(run_type="llm", name="input_guard_classification")
def classify_text_malicious(text: str) -> bool:
    """Return True when Prompt Guard labels the chunk malicious."""
    results = _input_guard_client().text_classification(
        text,
        model=config.llm.input_guard.model,
    )
    if not results:
        return False
    top = results[0]
    if not _is_malicious_label(top.label):
        return False
    threshold = config.llm.input_guard.malicious_score_threshold
    return top.score >= threshold


def resume_chunk_malicious(text: str) -> bool:
    """Scan resume chunks; fail closed on classifier errors."""
    chunks = _chunk_text(text, config.llm.input_guard.chunk_max_chars)
    try:
        return any(classify_text_malicious(chunk) for chunk in chunks)
    except Exception:
        logger.exception("input_guard classification failed")
        return True
