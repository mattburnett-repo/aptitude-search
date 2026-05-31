import json
from typing import Any

from app import prompt_loader
from app.llm import complete_chat_json, complete_chat_text
from app.models import Constraints
from app.validate import validate_stage

DEFAULT_CONSTRAINTS = Constraints()


def run_stage1(resume: str, model: str | None = None) -> Any:
    user = f"Analyze this resume and return the aptitude profile JSON.\n\n<resume>\n{resume}\n</resume>"
    result = complete_chat_json(
        prompt_loader.system_prompt_stage1(),
        user,
        model,
    )
    validate_stage("aptitudeProfile", result)
    return result


def run_stage2(
    aptitude_profile: Any,
    constraints: Constraints | None = None,
    model: str | None = None,
) -> str:
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    user = (
        "Find verified job openings for this candidate. "
        "Use web search to confirm each listing is currently active when possible.\n\n"
        f"<aptitude_profile>\n{json.dumps(aptitude_profile, indent=2)}\n</aptitude_profile>\n\n"
        f"<constraints>\n{c.model_dump_json(indent=2)}\n</constraints>"
    )
    return complete_chat_text(prompt_loader.system_prompt_stage2(), user, model)


def run_pipeline(
    resume: str,
    constraints: Constraints | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    aptitude_profile = run_stage1(resume, model)
    verified_matches = run_stage2(aptitude_profile, constraints, model)
    return {
        "aptitude_profile": aptitude_profile,
        "verified_matches": verified_matches,
    }
