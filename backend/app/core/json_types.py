"""Shared aliases and narrow helpers for loosely typed JSON dicts.

Pipeline stages pass around LLM/API payloads as plain dicts (not full Pydantic
models everywhere). These TypeAliases keep signatures consistent for the type
checker; ``as_object_dict`` / ``as_object_list`` safely narrow nested values
without repeating isinstance + cast. This module does not validate schemas —
that lives in ``validate.py``.

Stage payload aliases (``AptitudeProfile``, ``RoleFamilyPlan``,
``VerifiedMatches``) are still plain dicts; the names document intent only.
"""

from __future__ import annotations

from typing import TypeAlias, cast

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonObject: TypeAlias = dict[str, object]
FoundJob: TypeAlias = dict[str, object]
# Stage I/O labels (runtime shape still dict[str, object]; schema-checked elsewhere).
AptitudeProfile: TypeAlias = JsonObject
RoleFamilyPlan: TypeAlias = JsonObject
VerifiedMatches: TypeAlias = JsonObject
OccupationMatchJson: TypeAlias = JsonObject  # OccupationMatch.to_json() row
JsonValue: TypeAlias = JsonPrimitive | list[object] | JsonObject
JsonInstance: TypeAlias = JsonObject | list[object] | str | int | float | bool | None


def as_object_dict(value: object) -> JsonObject | None:
    if isinstance(value, dict):
        return cast(JsonObject, value)
    return None


def as_object_list(value: object) -> list[object] | None:
    if isinstance(value, list):
        return cast(list[object], value)
    return None
