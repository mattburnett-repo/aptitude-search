"""Compact Stage 2 inputs to keep agent context small."""

from typing import Any

from app import prompt_loader
from app.models import Constraints


def _labeled_names(items: list[Any] | None, *, limit: int = 8) -> str:
    """Pull names from a profile list and join them (e.g. skills → "Python, Django, Vue")."""
    names: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            label = item.get("name") or item.get("label")
            if label:
                names.append(str(label))
        elif item:
            names.append(str(item))
        if len(names) >= limit:
            break
    return ", ".join(names)


def compact_aptitude_profile_summary(profile: dict[str, Any]) -> str:
    """One short block for the agent (not full profile JSON)."""
    summary = (profile.get("aptitude_summary") or "").strip()
    if len(summary) > 400:
        summary = summary[:397].rstrip() + "..."
    lines = [
        f"seniority: {profile.get('seniority_band', 'unknown')}",
        f"core_skills: {_labeled_names(profile.get('core_skills'))}",
    ]
    secondary = _labeled_names(profile.get("secondary_skills"))
    if secondary:
        lines.append(f"secondary_skills: {secondary}")
    domains = _labeled_names(profile.get("domains"))
    if domains:
        lines.append(f"domains: {domains}")
    roles = _labeled_names(profile.get("adjacent_roles"))
    if roles:
        lines.append(f"adjacent_roles: {roles}")
    strengths = _labeled_names(profile.get("strengths"), limit=6)
    if strengths:
        lines.append(f"strengths: {strengths}")
    if summary:
        lines.append(f"summary: {summary}")
    return "\n".join(lines)


def build_stage2_user_message(
    aptitude_profile: Any,
    constraints: Constraints,
) -> str:
    profile = aptitude_profile if isinstance(aptitude_profile, dict) else {}
    compact = compact_aptitude_profile_summary(profile)
    constraints_json = constraints.model_dump_json()
    task = prompt_loader.user_task_stage2()
    return (
        f"{task}\n\n"
        f"<candidate_profile>\n{compact}\n</candidate_profile>\n\n"
        f"<constraints>\n{constraints_json}\n</constraints>"
    )
