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
