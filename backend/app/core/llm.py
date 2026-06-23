from huggingface_hub import InferenceClient
from huggingface_hub.inference._generated.types.chat_completion import (
    ChatCompletionInputResponseFormatJSONObject,
    ChatCompletionOutput,
)
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import JsonValue
from app.core.validate import parse_json_response


def _aptitude_client() -> InferenceClient:
    return InferenceClient(api_key=config.llm.aptitude.model_key)


def _chat_completion(
    client: InferenceClient,
    *,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int | None,
    json_object: bool,
) -> ChatCompletionOutput:
    response_format = (
        ChatCompletionInputResponseFormatJSONObject(type="json_object")
        if json_object
        else None
    )
    if max_tokens is not None and response_format is not None:
        return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
            messages=messages,
            model=config.llm.aptitude.model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
    if max_tokens is not None:
        return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
            messages=messages,
            model=config.llm.aptitude.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if response_format is not None:
        return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
            messages=messages,
            model=config.llm.aptitude.model,
            temperature=temperature,
            response_format=response_format,
        )
    return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
        messages=messages,
        model=config.llm.aptitude.model,
        temperature=temperature,
    )


@traceable(run_type="llm", name="stage1_aptitude_profile")
def complete_chat_json(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> JsonValue:
    """Hugging Face chat completion; returns parsed JSON."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    completion = _chat_completion(
        _aptitude_client(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=json_object,
    )
    choice = completion.choices[0]
    content = choice.message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    if choice.finish_reason == "length":
        raise RuntimeError(
            (
                "LLM response truncated (hit max_tokens). "
                "Increase llm.aptitude.max_tokens in config.toml or shorten model output."
            )
        )
    return parse_json_response(content)
