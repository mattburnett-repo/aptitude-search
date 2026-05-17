import json
from typing import Any

from app import prompt_loader
from app.llm import call_stage
from app.models import Constraints
from app.validate import validate_stage

DEFAULT_CONSTRAINTS = Constraints()


def run_stage1(api_key: str, resume: str, model: str | None = None) -> Any:
    user = f"Analyze this resume and return the aptitude profile JSON.\n\n<resume>\n{resume}\n</resume>"
    result = call_stage(
        api_key, prompt_loader.system_prompt_stage1(), user, model or "gpt-4o"
    )
    validate_stage("aptitudeProfile", result)
    return result


def run_stage2(
    api_key: str,
    aptitude_profile: Any,
    constraints: Constraints | None = None,
    model: str | None = None,
) -> Any:
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())
    user = (
        "Create a targeting strategy from this aptitude profile.\n\n"
        f"<aptitude_profile>\n{json.dumps(aptitude_profile, indent=2)}\n</aptitude_profile>\n\n"
        f"<constraints>\n{c.model_dump_json(indent=2)}\n</constraints>"
    )
    result = call_stage(
        api_key, prompt_loader.system_prompt_stage2(), user, model or "gpt-4o"
    )
    validate_stage("targetingStrategy", result)
    return result


def run_stage3(
    api_key: str, targeting_strategy: Any, model: str | None = None
) -> Any:
    user = (
        "Generate search queries from this targeting strategy.\n\n"
        f"<targeting_strategy>\n{json.dumps(targeting_strategy, indent=2)}\n</targeting_strategy>"
    )
    result = call_stage(
        api_key, prompt_loader.system_prompt_stage3(), user, model or "gpt-4o"
    )
    validate_stage("searchQueries", result)
    return result


def run_pipeline(
    api_key: str,
    resume: str,
    constraints: Constraints | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    aptitude_profile = run_stage1(api_key, resume, model)
    targeting_strategy = run_stage2(api_key, aptitude_profile, constraints, model)
    search_queries = run_stage3(api_key, targeting_strategy, model)
    return {
        "aptitude_profile": aptitude_profile,
        "targeting_strategy": targeting_strategy,
        "search_queries": search_queries,
    }


def run_iterate(
    api_key: str,
    regenerate_from_stage: int,
    current_artifacts: dict[str, Any],
    user_corrections: str,
    constraints: Constraints | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    c = constraints or DEFAULT_CONSTRAINTS
    user = (
        f"Apply my corrections and regenerate from stage {regenerate_from_stage}.\n\n"
        f"<current_artifacts>\n{json.dumps(current_artifacts, indent=2)}\n</current_artifacts>\n\n"
        f"<user_corrections>\n{user_corrections}\n</user_corrections>\n\n"
        f"<constraints>\n{c.model_dump_json(indent=2)}\n</constraints>"
    )
    result = call_stage(
        api_key, prompt_loader.system_prompt_stage4(), user, model or "gpt-4o"
    )
    if not isinstance(result, dict):
        raise ValueError("Iteration response must be a JSON object")

    if regenerate_from_stage == 2:
        if result.get("targeting_strategy"):
            validate_stage("targetingStrategy", result["targeting_strategy"])
        if result.get("search_queries"):
            validate_stage("searchQueries", result["search_queries"])
    else:
        if result.get("search_queries"):
            validate_stage("searchQueries", result["search_queries"])

    return result
