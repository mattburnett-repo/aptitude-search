import re

from app.paths import PROMPTS_DIR


def load_system_prompt(filename: str) -> str:
    content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    match = re.search(r"```\n([\s\S]*?)\n```", content)
    if not match:
        raise ValueError(f"Could not extract system prompt from {filename}")
    return match.group(1).strip()


def system_prompt_stage1() -> str:
    return load_system_prompt("01-resume-to-aptitude-profile.md")


def system_prompt_stage2() -> str:
    return load_system_prompt("02-verified-job-discovery.md")
