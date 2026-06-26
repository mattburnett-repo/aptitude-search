from huggingface_hub import InferenceClient
from huggingface_hub.inference._generated.types.chat_completion import (
    ChatCompletionInputResponseFormatJSONObject,
    ChatCompletionOutput,
)
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import JsonValue
from app.core.validate import parse_json_response


def _inference_client(api_key: str) -> InferenceClient:
    return InferenceClient(api_key=api_key)


def _chat_completion(
    client: InferenceClient,
    *,
    model: str,
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
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
    if max_tokens is not None:
        return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if response_format is not None:
        return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )
    return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
        messages=messages,
        model=model,
        temperature=temperature,
    )


def _complete_chat_json(
    *,
    client: InferenceClient,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
    max_tokens_config_key: str,
) -> JsonValue:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    completion = _chat_completion(
        client,
        model=model,
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
                f"Increase {max_tokens_config_key} in config.toml or shorten model output."
            )
        )
    return parse_json_response(content)


@traceable(run_type="llm", name="stage1_aptitude_profile")
def complete_chat_json(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> JsonValue:
    """Hugging Face chat completion for Stage 1/2; returns parsed JSON."""
    return _complete_chat_json(
        client=_inference_client(config.llm.aptitude.model_key),
        model=config.llm.aptitude.model,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=json_object,
        max_tokens_config_key="llm.aptitude.max_tokens",
    )


@traceable(run_type="llm", name="stage3_job_discovery_synthesis")
def complete_job_discovery_chat_json(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> JsonValue:
    """Hugging Face chat completion for Stage 3 synthesis; returns parsed JSON."""
    return _complete_chat_json(
        client=_inference_client(config.llm.job_discovery.model_key),
        model=config.llm.job_discovery.model,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=json_object,
        max_tokens_config_key="llm.job_discovery.max_tokens",
    )
