"""Stage 2: aptitude profile → role family plan."""

from __future__ import annotations

import json

from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core import prompt_loader
from app.core.config import config
from app.core.json_types import JsonObject
from app.core.llm import complete_chat_json
from app.core.progress import ProgressCallback, emit_progress
from app.core.validate import normalize_role_family_plan, validate_stage


@traceable(run_type="chain", name="stage2")
def run_stage2(
    aptitude_profile: JsonObject,
    *,
    on_progress: ProgressCallback | None = None,
) -> JsonObject:
    emit_progress("Stage 2: Building role family plan…", on_progress=on_progress)
    task = prompt_loader.user_task_role_family_plan()
    profile_json = json.dumps(aptitude_profile, indent=2)
    user = f"{task}\n\n<aptitude_profile>\n{profile_json}\n</aptitude_profile>"
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
    return result
