from huggingface_hub import InferenceClient
from huggingface_hub.inference._generated.types.chat_completion import (
    ChatCompletionInputResponseFormatJSONObject,
)
from langsmith import traceable

from app.core.config import config
from app.core.validate import parse_json_response


def _aptitude_client() -> InferenceClient:
    return InferenceClient(api_key=config.llm.aptitude.model_key)


@traceable(run_type="llm", name="stage1_aptitude_profile")
def complete_chat_json(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> object:
    """Hugging Face chat completion; returns parsed JSON."""
    kwargs: dict = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "model": config.llm.aptitude.model,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if json_object:
        kwargs["response_format"] = ChatCompletionInputResponseFormatJSONObject(
            type="json_object"
        )
    completion = _aptitude_client().chat_completion(**kwargs)
    choice = completion.choices[0]
    content = choice.message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    if choice.finish_reason == "length":
        raise RuntimeError(
            "LLM response truncated (hit max_tokens). "
            "Increase llm.aptitude.max_tokens in config.toml or shorten model output."
        )
    return parse_json_response(content)
