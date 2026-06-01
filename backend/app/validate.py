import json
import re
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema import RefResolver

from app.config import config
from app.paths import SCHEMAS_DIR


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _build_validators() -> dict[str, Draft202012Validator]:
    constraints = _load_schema(config.schemas.constraints)
    aptitude = _load_schema(config.schemas.aptitude_profile)
    store = {
        constraints["$id"]: constraints,
        aptitude["$id"]: aptitude,
    }
    return {
        "aptitudeProfile": Draft202012Validator(
            aptitude, resolver=RefResolver.from_schema(aptitude, store=store)
        ),
        "constraints": Draft202012Validator(
            constraints, resolver=RefResolver.from_schema(constraints, store=store)
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


def validate_stage(stage: str, data: Any) -> None:
    validator = _VALIDATORS.get(stage)
    if validator is None:
        raise ValueError(f"Unknown stage: {stage}")
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msg = "; ".join(e.message for e in errors[:5])
        raise ValueError(f"Schema validation failed ({stage}): {msg}")


def parse_json_response(text: str) -> Any:
    trimmed = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```$", trimmed)
    return json.loads(fence.group(1).strip() if fence else trimmed)


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
