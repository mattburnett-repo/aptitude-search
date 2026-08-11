"""Helpers that turn JSON list fields into plain text for discovery and prompts.

- ``profile_labels`` / ``labeled_names`` — aptitude profile skill and labeled
  items (``name`` or ``label`` on each object).
- ``string_list`` / ``joined_strings`` — role-family plan arrays of bare
  strings (``search_terms``, ``work_modes``, ``avoid_terms``).
"""

from app.core.json_types import as_object_dict, as_object_list


def profile_labels(items: object, *, limit: int | None = None) -> list[str]:
    """Pull name/label strings from a profile list field (skill/labeled items)."""
    names: list[str] = []
    item_list = as_object_list(items)
    if item_list is None:
        return names
    for item in item_list:
        item_dict = as_object_dict(item)
        if item_dict is None:
            continue
        raw = item_dict.get("name") or item_dict.get("label")
        if not raw:
            continue
        label = str(raw).strip()
        if not label or label in names:
            continue
        names.append(label)
        if limit is not None and len(names) >= limit:
            break
    return names


def string_list(
    items: object,
    *,
    limit: int | None = None,
    lowercase: bool = False,
) -> list[str]:
    """Normalize a JSON array of plain strings (role-family plan fields).

    Use for schema fields like ``search_terms``, ``work_modes``, and
    ``avoid_terms`` — not for aptitude profile skill/labeled objects
    (those go through ``profile_labels``).

    Skips non-strings and blanks, dedupes while preserving order, optionally
    lowercases, and stops after ``limit`` values when set.
    """
    values: list[str] = []
    item_list = as_object_list(items)
    if item_list is None:
        return values
    seen: set[str] = set()
    for item in item_list:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if lowercase:
            text = text.lower()
        if not text or text in seen:
            continue
        seen.add(text)
        values.append(text)
        if limit is not None and len(values) >= limit:
            break
    return values


def labeled_names(items: object, *, limit: int = 8) -> str:
    """Comma-joined profile labels (e.g. skills → "Python, Django, Vue")."""
    return ", ".join(profile_labels(items, limit=limit))


def joined_strings(items: object, *, limit: int = 8) -> str:
    """Comma-joined plain strings (e.g. search_terms → "backend engineer, …")."""
    return ", ".join(string_list(items, limit=limit))
