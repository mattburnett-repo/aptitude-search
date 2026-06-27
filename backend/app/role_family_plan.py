"""Stage 2: aptitude profile → role family plan."""

from __future__ import annotations

import json
from dataclasses import dataclass

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import prompt_loader
from app.core.config import config
from app.core.json_types import JsonObject
from app.core.llm import complete_chat_json
from app.core.progress import ProgressCallback, emit_progress
from app.core.validate import normalize_role_family_plan, validate_stage
from app.onet.match import (
    OccupationMatch,
    format_matches_for_prompt,
    match_aptitude_to_occupations,
)


@dataclass(frozen=True)
class Stage2Result:
    role_family_plan: JsonObject
    occupation_matches: tuple[OccupationMatch, ...] = ()


@traceable(run_type="chain", name="stage2")
def run_stage2(
    aptitude_profile: JsonObject,
    *,
    on_progress: ProgressCallback | None = None,
) -> Stage2Result:
    emit_progress("Stage 2: Matching aptitude to O*NET occupations…", on_progress=on_progress)
    occupation_matches = tuple(match_aptitude_to_occupations(aptitude_profile))
    if occupation_matches:
        emit_progress(
            f"Stage 2: Top O*NET match — {occupation_matches[0].title}.",
            on_progress=on_progress,
        )

    emit_progress("Stage 2: Building role family plan…", on_progress=on_progress)
    task = prompt_loader.user_task_role_family_plan()
    profile_json = json.dumps(aptitude_profile, indent=2)
    onet_block = ""
    if occupation_matches:
        onet_block = (
            "\n\n<onet_occupation_matches>\n"
            f"{format_matches_for_prompt(list(occupation_matches))}\n"
            "Ground recommended_role_families and search_terms in these matches "
            "where they fit the aptitude profile.\n"
            "</onet_occupation_matches>"
        )
    user = (
        f"{task}\n\n<aptitude_profile>\n{profile_json}\n</aptitude_profile>{onet_block}"
    )
    result = normalize_role_family_plan(
        complete_chat_json(
            prompt_loader.system_prompt_role_family_plan(),
            user,
            temperature=config.llm.aptitude.temperature,
            max_tokens=config.llm.aptitude.max_tokens,
            json_object=True,
        )
    )
    validate_stage("roleFamilyPlan", result)
    emit_progress("Stage 2 complete.", on_progress=on_progress)
    return Stage2Result(
        role_family_plan=result,
        occupation_matches=occupation_matches,
    )
