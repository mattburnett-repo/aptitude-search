import json
import re
from typing import cast

from jsonschema import Draft202012Validator
from jsonschema import RefResolver  # pyright: ignore[reportDeprecated]
from jsonschema.exceptions import ValidationError

from app.core.config import config
from app.core.json_types import (
    JsonInstance,
    JsonObject,
    JsonValue,
    as_object_dict,
    as_object_list,
)
from app.core.paths import SCHEMAS_DIR


def _load_schema(name: str) -> JsonObject:
    return cast(JsonObject, json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8")))


def _build_validators() -> dict[str, Draft202012Validator]:
    constraints = _load_schema(config.schemas.constraints)
    aptitude = _load_schema(config.schemas.aptitude_profile)
    job_discovery = _load_schema(config.schemas.job_discovery_results)
    store: dict[str, JsonObject] = {
        str(constraints["$id"]): constraints,
        str(aptitude["$id"]): aptitude,
        str(job_discovery["$id"]): job_discovery,
    }
    return {
        "aptitudeProfile": Draft202012Validator(
            aptitude,
            resolver=RefResolver.from_schema(  # pyright: ignore[reportDeprecated, reportUnknownMemberType]
                aptitude, store=store
            ),
        ),
        "constraints": Draft202012Validator(
            constraints,
            resolver=RefResolver.from_schema(  # pyright: ignore[reportDeprecated, reportUnknownMemberType]
                constraints, store=store
            ),
        ),
        "jobDiscovery": Draft202012Validator(
            job_discovery,
            resolver=RefResolver.from_schema(  # pyright: ignore[reportDeprecated, reportUnknownMemberType]
                job_discovery, store=store
            ),
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


def validate_stage(stage: str, data: JsonInstance) -> None:
    validator = _VALIDATORS.get(stage)
    if validator is None:
        raise ValueError(f"Unknown stage: {stage}")
    errors = sorted(
        cast(
            list[ValidationError],
            list(
                validator.iter_errors(data)  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            ),
        ),
        key=lambda error: list(error.path),
    )
    if errors:
        msg = "; ".join(error.message for error in errors[:5])
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


def _loads_json_lenient(payload: str) -> JsonValue:
    attempts = (
        payload,
        re.sub(r",\s*([\]}])", r"\1", payload),
    )
    last_error: json.JSONDecodeError | None = None
    for candidate in attempts:
        try:
            return cast(JsonValue, json.loads(candidate))
        except json.JSONDecodeError as e:
            last_error = e
            try:
                return cast(
                    JsonValue,
                    json.JSONDecoder().raw_decode(candidate.lstrip())[0],
                )
            except json.JSONDecodeError as e2:
                last_error = e2
    assert last_error is not None
    raise last_error


def parse_json_response(text: str) -> JsonValue:
    """Parse JSON from LLM/agent text (fenced block, embedded fence, or raw object)."""
    payload = _json_payload_from_text(text)
    try:
        return _loads_json_lenient(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in model response: {e}") from e


def _normalize_confidence(value: object) -> str:
    if isinstance(value, str) and value in _VALID_CONFIDENCE:
        return value
    return "low"


def _normalize_confidence_map_entry(item: object) -> dict[str, str]:
    """Coerce LLM confidence_map values into {confidence, reason}."""
    if isinstance(item, str):
        return {"confidence": _normalize_confidence(item), "reason": ""}
    entry = as_object_dict(item)
    if entry is None:
        return {"confidence": "low", "reason": ""}

    confidence = entry.get("confidence")
    reason = entry.get("reason")
    if isinstance(confidence, str) and confidence in _VALID_CONFIDENCE:
        return {
            "confidence": confidence,
            "reason": reason.strip() if isinstance(reason, str) else "",
        }

    for level in ("high", "medium", "low"):
        level_val = entry.get(level)
        if isinstance(level_val, str) and level_val.strip():
            return {"confidence": level, "reason": level_val.strip()}
        if level_val is True:
            return {"confidence": level, "reason": ""}

    if isinstance(reason, str) and reason.strip():
        return {"confidence": "low", "reason": reason.strip()}

    return {"confidence": "low", "reason": ""}


def _normalize_confidence_map(confidence_map: object) -> dict[str, dict[str, str]]:
    mapping = as_object_dict(confidence_map)
    if mapping is None:
        return {}

    if mapping and all(str(key) in _VALID_CONFIDENCE for key in mapping):
        rebuilt: dict[str, dict[str, str]] = {}
        for level, fields in mapping.items():
            field_names: list[str] = []
            field_list = as_object_list(fields)
            if field_list is not None:
                field_names = [str(field) for field in field_list if field]
            elif isinstance(fields, str) and fields.strip():
                field_names = [fields.strip()]
            for field in field_names:
                rebuilt[field] = {
                    "confidence": _normalize_confidence(str(level)),
                    "reason": "",
                }
        return rebuilt

    return {
        str(key): _normalize_confidence_map_entry(item)
        for key, item in mapping.items()
    }


def _prune_dict(item: JsonObject, allowed: frozenset[str]) -> None:
    for key in list(item.keys()):
        if key not in allowed:
            del item[key]


_SKILL_ITEM_KEYS = frozenset({"name", "confidence", "evidence_from_resume"})
_LABELED_ITEM_KEYS = frozenset({"label", "confidence", "evidence_from_resume"})


def _normalize_seniority_band(value: object) -> str:
    if not isinstance(value, str):
        return "unknown"
    key = value.strip().lower()
    if key in _VALID_SENIORITY:
        return key
    return _SENIORITY_ALIASES.get(key, "unknown")


def _normalize_skill_item(item: JsonObject) -> None:
    name = item.get("name")
    label = item.get("label")
    if not isinstance(name, str) or not name.strip():
        if isinstance(label, str) and label.strip():
            item["name"] = label.strip()
    _prune_dict(item, _SKILL_ITEM_KEYS)
    item["confidence"] = _normalize_confidence(item.get("confidence"))


def _normalize_labeled_item(item: JsonObject) -> None:
    label = item.get("label")
    name = item.get("name")
    if not isinstance(label, str) or not label.strip():
        if isinstance(name, str) and name.strip():
            item["label"] = name.strip()
    _prune_dict(item, _LABELED_ITEM_KEYS)
    item["confidence"] = _normalize_confidence(item.get("confidence"))


def normalize_aptitude_profile(data: object) -> JsonObject:
    profile = as_object_dict(data)
    if profile is None:
        return {}

    profile["seniority_band"] = _normalize_seniority_band(profile.get("seniority_band"))

    for key in ("core_skills", "secondary_skills"):
        items = as_object_list(profile.get(key))
        if items is None:
            continue
        for item in items:
            skill_item = as_object_dict(item)
            if skill_item is not None:
                _normalize_skill_item(skill_item)

    for key in ("domains", "strengths", "adjacent_roles", "working_style_signals"):
        items = as_object_list(profile.get(key))
        if items is None:
            continue
        for item in items:
            labeled_item = as_object_dict(item)
            if labeled_item is not None:
                _normalize_labeled_item(labeled_item)

    profile["confidence_map"] = _normalize_confidence_map(profile.get("confidence_map"))
    return profile


def _build_match_description(item: JsonObject) -> str:
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
        val_list = as_object_list(val)
        if val_list:
            parts.append(
                f"{key.replace('_', ' ')}: {', '.join(str(entry) for entry in val_list)}"
            )
        elif isinstance(val, str) and val.strip():
            parts.append(val.strip())

    if parts:
        return " ".join(parts)

    role = item.get("role") or item.get("title") or "role"
    company = item.get("company") or "employer"
    return f"Aligned with aptitude profile for {role} at {company}."


def normalize_job_discovery_results(data: object) -> JsonObject:
    payload = as_object_dict(data)
    if payload is None:
        return {}

    results = as_object_list(payload.get("results"))
    if results is None:
        return payload

    normalized: list[JsonObject] = []
    for item in results:
        row = as_object_dict(item)
        if row is None:
            continue
        if "role" not in row and isinstance(row.get("title"), str):
            row["role"] = row["title"]
        row["match_description"] = _build_match_description(row)
        if "seniority_level" in row:
            row["seniority_level"] = _normalize_seniority_band(row.get("seniority_level"))
        if isinstance(row.get("confidence"), str):
            row["confidence"] = _normalize_confidence(row.get("confidence"))
        normalized.append({key: value for key, value in row.items() if key in _JOB_POSTING_KEYS})

    payload["results"] = normalized
    return payload
