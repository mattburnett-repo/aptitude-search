"""Shared types for parsed JSON and pipeline dict payloads."""

from __future__ import annotations

from typing import TypeAlias, cast

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonObject: TypeAlias = dict[str, object]
FoundJob: TypeAlias = dict[str, object]
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
