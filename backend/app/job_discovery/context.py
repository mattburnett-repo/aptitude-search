"""Compact Stage 2 inputs for synthesis LLM context."""

import json

from app.core import prompt_loader
from app.core.json_types import FoundJob, JsonObject, as_object_dict, as_object_list
from app.core.models import Constraints


def labeled_names(items: object, *, limit: int = 8) -> str:
    """Pull names from a profile list and join them (e.g. skills → "Python, Django, Vue")."""
    names: list[str] = []
    item_list = as_object_list(items)
    if item_list is None:
        return ", ".join(names)
    for item in item_list:
        item_dict = as_object_dict(item)
        if item_dict is not None:
            label = item_dict.get("name") or item_dict.get("label")
            if label:
                names.append(str(label))
        elif item:
            names.append(str(item))
        if len(names) >= limit:
            break
    return ", ".join(names)


def compact_aptitude_profile_summary(profile: JsonObject) -> str:
    """One short block for synthesis (not full profile JSON)."""
    summary_raw = profile.get("aptitude_summary")
    summary = summary_raw.strip() if isinstance(summary_raw, str) else ""
    if len(summary) > 400:
        summary = summary[:397].rstrip() + "..."
    lines = [
        f"seniority: {profile.get('seniority_band', 'unknown')}",
        f"core_skills: {labeled_names(profile.get('core_skills'))}",
    ]
    secondary = labeled_names(profile.get("secondary_skills"))
    if secondary:
        lines.append(f"secondary_skills: {secondary}")
    domains = labeled_names(profile.get("domains"))
    if domains:
        lines.append(f"domains: {domains}")
    roles = labeled_names(profile.get("adjacent_roles"))
    if roles:
        lines.append(f"adjacent_roles: {roles}")
    strengths = labeled_names(profile.get("strengths"), limit=6)
    if strengths:
        lines.append(f"strengths: {strengths}")
    if summary:
        lines.append(f"summary: {summary}")
    return "\n".join(lines)


def build_stage2_synthesis_user_message(
    aptitude_profile: JsonObject,
    constraints: Constraints,
    found_jobs: list[FoundJob],
) -> str:
    compact = compact_aptitude_profile_summary(aptitude_profile)
    constraints_json = constraints.model_dump_json()
    jobs_json = json.dumps(found_jobs, indent=2)
    task = prompt_loader.user_task_stage2_synthesis()
    return (
        f"{task}\n\n"
        f"<candidate_profile>\n{compact}\n</candidate_profile>\n\n"
        f"<constraints>\n{constraints_json}\n</constraints>\n\n"
        f"<found_jobs>\n{jobs_json}\n</found_jobs>"
    )
