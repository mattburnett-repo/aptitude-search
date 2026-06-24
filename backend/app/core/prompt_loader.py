from app.core.config import config
from app.core.paths import PROMPTS_DIR


def load_system_prompt(filename: str) -> str:
    content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return content.strip()


def system_prompt_stage1() -> str:
    return load_system_prompt(config.prompts.stage1_file)


def system_prompt_stage2_synthesis() -> str:
    return load_system_prompt(config.prompts.stage2_synthesis_file)


def system_prompt_role_family_plan() -> str:
    return load_system_prompt(config.prompts.stage1_5_file)


def system_prompt_stage2() -> str:
    """Alias for synthesis prompt (schema JSON phase)."""
    return system_prompt_stage2_synthesis()


def _load_user_task_file(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def user_task_stage1() -> str:
    """Runtime user message preamble for Stage 1 (resume → aptitude profile JSON)."""
    return _load_user_task_file(config.prompts.stage1_user_task_file)


def user_task_role_family_plan() -> str:
    """Runtime user message preamble for Stage 1.5 (profile → role family plan JSON)."""
    return _load_user_task_file(config.prompts.stage1_5_user_task_file)


def user_task_stage2_synthesis() -> str:
    """Runtime user message preamble for the Stage 2 synthesis LLM call."""
    return _load_user_task_file(config.prompts.stage2_synthesis_user_task_file)
