"""Load Stage 1–3 system prompts and user-task preambles from ``prompts/``.

- Filenames come from ``[prompts]`` in ``config.toml`` (via ``config.prompts``).
- System prompts are Markdown; a leading ``# `` title line is stripped.
- User-task files are plain-text preambles for the runtime user message.
"""

from app.core.config import config
from app.core.paths import PROMPTS_DIR


def load_system_prompt(filename: str) -> str:
    """Read a Markdown system prompt from ``PROMPTS_DIR``.

    - Drops a leading ``# `` title line when present.
    - Returns the remaining body stripped.
    - Used by the stage-specific system-prompt wrappers below.
    """
    content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return content.strip()


def system_prompt_stage1() -> str:
    """System prompt for Stage 1.

    - Input: resume text
    - Output: AptitudeProfile JSON
    """
    return load_system_prompt(config.prompts.stage1_file)


def system_prompt_stage2() -> str:
    """System prompt for Stage 2.

    - Input: AptitudeProfile
    - Output: RoleFamilyPlan JSON
    """
    return load_system_prompt(config.prompts.stage2_file)


def system_prompt_stage3_synthesis() -> str:
    """System prompt for Stage 3 synthesis.

    - Input: found jobs (+ profile/plan context)
    - Output: verified_matches JSON
    """
    return load_system_prompt(config.prompts.stage3_synthesis_file)


def _load_user_task_file(filename: str) -> str:
    """Read a user-task preamble from ``PROMPTS_DIR``.

    - Shared by ``user_task_stage1`` / ``user_task_stage2`` / ``user_task_stage3_synthesis``.
    - Those preambles are prepended to the runtime user message in ``pipeline.py``
      (Stages 1–2) and ``job_discovery/context.py`` (Stage 3 synthesis).
    - No title stripping (unlike ``load_system_prompt``); these files are short
      plain text, not Markdown with an H1.
    - Returns the file contents stripped.
    """
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def user_task_stage1() -> str:
    """User-message preamble for Stage 1.

    - Prepended to the resume payload
    - Guides resume → aptitude profile JSON
    """
    return _load_user_task_file(config.prompts.stage1_user_task_file)


def user_task_stage2() -> str:
    """User-message preamble for Stage 2.

    - Prepended to the profile (+ O*NET context) payload
    - Guides profile → role family plan JSON
    """
    return _load_user_task_file(config.prompts.stage2_user_task_file)


def user_task_stage3_synthesis() -> str:
    """User-message preamble for Stage 3 synthesis.

    - Prepended to the synthesis context payload
    - Guides found jobs → verified matches JSON
    """
    return _load_user_task_file(config.prompts.stage3_synthesis_user_task_file)
