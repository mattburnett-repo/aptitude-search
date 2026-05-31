from openai import OpenAI

from app.config import config
from app.validate import parse_json_response


def _client() -> OpenAI:
    return OpenAI(api_key=config.llm.api_key)


def complete_chat_json(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> object:
    """OpenAI chat completion with JSON response mode; returns parsed JSON."""
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


def complete_chat_text(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> str:
    """OpenAI chat completion returning plain text (no JSON response mode)."""
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
