import re

from app.config import config
from app.paths import PROMPTS_DIR


def load_system_prompt(filename: str) -> str:
    content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    match = re.search(r"```\n([\s\S]*?)\n```", content)
    if match:
        return match.group(1).strip()
    # Schema-strict prompts: entire file is the system prompt (skip markdown title line).
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return content.strip()


def system_prompt_stage1() -> str:
    return load_system_prompt(config.prompts.stage1_file)


def system_prompt_stage2() -> str:
    return load_system_prompt(config.prompts.stage2_file)
