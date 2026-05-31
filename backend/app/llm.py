from openai import OpenAI

from app.config import config
from app.validate import parse_json_response


def _client() -> OpenAI:
    return OpenAI(api_key=config.llm.api_key)


def call_stage(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> object:
    """Pipeline stage 1: LLM call that must return JSON (aptitude profile).

    "Stage" means a step in the two-prompt flow (see run_stage1 / run_stage2),
    not a parameter. Stage 2 uses call_stage_text instead.
    """
    completion = _client().chat.completions.create(
        model=model or config.llm.default_model,
        temperature=config.llm.temperature,
        response_format={"type": config.llm.json_response_type},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    return parse_json_response(content)


def call_stage_text(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> str:
    """Pipeline stage 2: LLM call returning plain text (verified job discovery)."""
    completion = _client().chat.completions.create(
        model=model or config.llm.default_model,
        temperature=config.llm.temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    return content.strip()
