import math

import numpy as np
import pytest

from app.core.embedding import (
    _parse_embeddings,
    flatten_embedding,
    normalize_embedding,
    aptitude_text_for_embedding,
)


def test_flatten_embedding_accepts_flat_vector() -> None:
    assert flatten_embedding([0.1, 0.2, 0.3], expected_dim=3) == [0.1, 0.2, 0.3]


def test_flatten_embedding_mean_pools_token_rows() -> None:
    raw = [[1.0, 0.0], [3.0, 2.0]]
    assert flatten_embedding(raw, expected_dim=2) == [2.0, 1.0]


def test_flatten_embedding_accepts_numpy_token_matrix() -> None:
    raw = np.array([[1.0, 0.0], [3.0, 2.0]], dtype=np.float32)
    assert flatten_embedding(raw, expected_dim=2) == [2.0, 1.0]


def test_parse_embeddings_batch_numpy() -> None:
    raw = np.array(
        [
            [[1.0, 0.0], [3.0, 2.0]],
            [[0.0, 1.0], [2.0, 3.0]],
        ],
        dtype=np.float32,
    )
    result = _parse_embeddings(raw, expected_dim=2, expected_count=2)
    assert result == [[2.0, 1.0], [1.0, 2.0]]


def test_normalize_embedding_unit_length() -> None:
    vector = normalize_embedding([3.0, 4.0])
    assert math.isclose(math.sqrt(sum(x * x for x in vector)), 1.0)


def test_aptitude_text_for_embedding_uses_work_pattern_fields() -> None:
    profile = {
        "aptitude_summary": "Builder who modernizes legacy systems.",
        "strengths": [{"name": "End-to-end ownership", "confidence": "high"}],
        "working_style_signals": [{"name": "High ambiguity tolerance", "confidence": "high"}],
    }
    text = aptitude_text_for_embedding(profile)
    assert "Summary: Builder who modernizes legacy systems." in text
    assert "Strengths: End-to-end ownership" in text
    assert "Work style: High ambiguity tolerance" in text
    assert "Python" not in text


def test_aptitude_text_for_embedding_requires_content() -> None:
    with pytest.raises(ValueError, match="no embeddable text"):
        aptitude_text_for_embedding({})
