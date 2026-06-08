import json
import re
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema import RefResolver

from app.core.config import config
from app.core.paths import SCHEMAS_DIR


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _build_validators() -> dict[str, Draft202012Validator]:
    constraints = _load_schema(config.schemas.constraints)
    aptitude = _load_schema(config.schemas.aptitude_profile)
    job_discovery = _load_schema(config.schemas.job_discovery_results)
    store = {
        constraints["$id"]: constraints,
        aptitude["$id"]: aptitude,
        job_discovery["$id"]: job_discovery,
    }
    return {
        "aptitudeProfile": Draft202012Validator(
            aptitude, resolver=RefResolver.from_schema(aptitude, store=store)
        ),
        "constraints": Draft202012Validator(
            constraints, resolver=RefResolver.from_schema(constraints, store=store)
        ),
        "jobDiscovery": Draft202012Validator(
            job_discovery, resolver=RefResolver.from_schema(job_discovery, store=store)
        ),
    }


_VALIDATORS = _build_validators()
_VALID_CONFIDENCE = {"high", "medium", "low"}
_VALID_SENIORITY = {
    "entry",
    "mid",
    "senior",
    "staff",
    "principal",
    "executive",
    "unknown",
}
_SENIORITY_ALIASES = {"mid-level": "mid"}
_JOB_POSTING_KEYS = frozenset(
    {
        "company",
        "role",
        "url",
        "match_description",
        "location",
        "employment_type",
        "seniority_level",
        "match_signals",
        "confidence",
    }
)


def validate_stage(stage: str, data: Any) -> None:
    validator = _VALIDATORS.get(stage)
    if validator is None:
        raise ValueError(f"Unknown stage: {stage}")
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msg = "; ".join(e.message for e in errors[:5])
        raise ValueError(f"Schema validation failed ({stage}): {msg}")


def _json_payload_from_text(text: str) -> str:
    trimmed = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", trimmed)
    if fence:
        return fence.group(1).strip()
    start = trimmed.find("{")
    if start >= 0:
        return trimmed[start:]
    return trimmed


def _loads_json_lenient(payload: str) -> Any:
    attempts = (
        payload,
        re.sub(r",\s*([\]}])", r"\1", payload),
    )
    last_error: json.JSONDecodeError | None = None
    for candidate in attempts:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            last_error = e
            try:
                obj, _end = json.JSONDecoder().raw_decode(candidate.lstrip())
                return obj
            except json.JSONDecodeError as e2:
                last_error = e2
    assert last_error is not None
    raise last_error


def parse_json_response(text: str) -> Any:
    """Parse JSON from LLM/agent text (fenced block, embedded fence, or raw object)."""
    payload = _json_payload_from_text(text)
    try:
        return _loads_json_lenient(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in model response: {e}") from e


def _normalize_confidence(value: Any) -> str:
    if isinstance(value, str) and value in _VALID_CONFIDENCE:
        return value
    return "low"


def _normalize_seniority_band(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"
    key = value.strip().lower()
    if key in _VALID_SENIORITY:
        return key
    return _SENIORITY_ALIASES.get(key, "unknown")


def normalize_aptitude_profile(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    data["seniority_band"] = _normalize_seniority_band(data.get("seniority_band"))

    skill_keys = ("core_skills", "secondary_skills")
    labeled_keys = ("domains", "strengths", "adjacent_roles", "working_style_signals")

    for key in skill_keys + labeled_keys:
        items = data.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                item["confidence"] = _normalize_confidence(item.get("confidence"))

    confidence_map = data.get("confidence_map")
    if isinstance(confidence_map, dict):
        for item in confidence_map.values():
            if isinstance(item, dict):
                item["confidence"] = _normalize_confidence(item.get("confidence"))

    return data


def _build_match_description(item: dict) -> str:
    existing = item.get("match_description")
    if isinstance(existing, str) and existing.strip():
        return existing.strip()

    parts: list[str] = []
    for key in (
        "match_signals",
        "core_skills_match",
        "secondary_skills_match",
        "strengths_match",
        "adjacent_roles_match",
    ):
        val = item.get(key)
        if isinstance(val, list) and val:
            parts.append(f"{key.replace('_', ' ')}: {', '.join(str(x) for x in val)}")
        elif isinstance(val, str) and val.strip():
            parts.append(val.strip())

    if parts:
        return " ".join(parts)

    role = item.get("role") or item.get("title") or "role"
    company = item.get("company") or "employer"
    return f"Aligned with aptitude profile for {role} at {company}."


def normalize_job_discovery_results(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    results = data.get("results")
    if not isinstance(results, list):
        return data

    normalized: list[Any] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if "role" not in item and isinstance(item.get("title"), str):
            item["role"] = item["title"]
        item["match_description"] = _build_match_description(item)
        if "seniority_level" in item:
            item["seniority_level"] = _normalize_seniority_band(item.get("seniority_level"))
        if isinstance(item.get("confidence"), str):
            item["confidence"] = _normalize_confidence(item.get("confidence"))
        normalized.append({k: v for k, v in item.items() if k in _JOB_POSTING_KEYS})

    data["results"] = normalized
    return data
