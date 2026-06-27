"""Aptitude profile → O*NET occupation vector search (pgvector)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import config as config_module
from app.core.embedding import embed_aptitude_profile, vector_literal
from app.core.json_types import JsonObject

logger = logging.getLogger(__name__)

MATCH_SQL = """
SELECT
  oe.onetsoc_code,
  od.title,
  oe.occupation_profile,
  1 - (oe.embedding <=> %s::vector) AS score
FROM occupation_embeddings oe
JOIN occupation_data od ON od.onetsoc_code = oe.onetsoc_code
ORDER BY oe.embedding <=> %s::vector
LIMIT %s
"""


@dataclass(frozen=True)
class OccupationMatch:
    onetsoc_code: str
    title: str
    score: float
    occupation_profile: str

    def to_json(self) -> JsonObject:
        return {
            "onetsoc_code": self.onetsoc_code,
            "title": self.title,
            "score": round(self.score, 4),
        }


def matches_to_json(matches: list[OccupationMatch]) -> list[JsonObject]:
    return [match.to_json() for match in matches]


def _truncate(text: str, *, max_chars: int = 240) -> str:
    stripped = text.strip()
    if len(stripped) <= max_chars:
        return stripped
    return stripped[: max_chars - 3].rstrip() + "..."


def format_matches_for_prompt(matches: list[OccupationMatch]) -> str:
    if not matches:
        return ""
    lines = [
        "O*NET vector matches (primary grounding for role_family and search_terms):",
    ]
    for index, match in enumerate(matches, start=1):
        lines.append(
            f"{index}. {match.title} ({match.onetsoc_code}) — similarity {match.score:.3f}"
        )
        lines.append(f"   {_truncate(match.occupation_profile)}")
    return "\n".join(lines)


@traceable(run_type="retriever", name="onet_occupation_match")
def match_aptitude_to_occupations(
    aptitude_profile: JsonObject,
    *,
    top_k: int | None = None,
) -> list[OccupationMatch]:
    """Return top-K O*NET occupations by cosine similarity to the aptitude profile."""
    matching = config_module.config.onet_matching
    if not matching.enabled:
        return []

    limit = top_k if top_k is not None else matching.top_k
    if limit < 1:
        return []

    try:
        query_vector = embed_aptitude_profile(aptitude_profile)
    except Exception:
        logger.exception("onet matching: failed to embed aptitude profile")
        return []

    vector_param = vector_literal(query_vector)

    try:
        from app.core.onet_db import connect

        with connect() as conn:
            with conn.cursor() as cur:
                _ = cur.execute(MATCH_SQL, (vector_param, vector_param, limit))
                rows = cur.fetchall()
    except Exception:
        logger.exception("onet matching: postgres query failed")
        return []

    matches: list[OccupationMatch] = []
    for onetsoc_code, title, occupation_profile, score in rows:
        score_value = float(score)
        if score_value < matching.min_similarity:
            continue
        matches.append(
            OccupationMatch(
                onetsoc_code=onetsoc_code.strip(),
                title=title.strip(),
                score=score_value,
                occupation_profile=occupation_profile.strip(),
            )
        )
    return matches
