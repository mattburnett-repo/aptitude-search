"""Shared helpers for aptitude profile list fields → text."""

from app.core.json_types import as_object_dict, as_object_list


def profile_labels(items: object, *, limit: int | None = None) -> list[str]:
    """Pull name/label strings from a profile list field."""
    names: list[str] = []
    item_list = as_object_list(items)
    if item_list is None:
        return names
    for item in item_list:
        label: str | None = None
        item_dict = as_object_dict(item)
        if item_dict is not None:
            raw = item_dict.get("name") or item_dict.get("label")
            if raw:
                label = str(raw).strip()
        elif item:
            label = str(item).strip()
        if not label or label in names:
            continue
        names.append(label)
        if limit is not None and len(names) >= limit:
            break
    return names


def labeled_names(items: object, *, limit: int = 8) -> str:
    """Comma-joined profile labels (e.g. skills → "Python, Django, Vue")."""
    return ", ".join(profile_labels(items, limit=limit))
