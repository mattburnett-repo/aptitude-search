"""Hugging Face chat helpers for schema-strict JSON stage outputs.

Shared call/parse logic lives in ``_llm_call``. The two public wrappers bind
config + LangSmith spans so callers never pass credentials:

- ``aptitude_llm_call`` → ``[llm.aptitude]`` (Stages 1 and 2)
- ``job_discovery_llm_call`` → ``[llm.job_discovery]`` (Stage 3 synthesis)
"""

from huggingface_hub import InferenceClient
from huggingface_hub.inference._generated.types.chat_completion import (
    ChatCompletionInputResponseFormatJSONObject,
    ChatCompletionOutput,
)
from langsmith import traceable  # pyright: ignore[reportUnknownVariableType]

from app.core.config import config
from app.core.json_types import JsonValue
from app.core.validate import parse_json_response


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
    return client.chat_completion(  # pyright: ignore[reportUnknownMemberType]
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        stream=False,
    )


def _llm_call(
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
def aptitude_llm_call(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> JsonValue:
    """Stages 1/2: ``[llm.aptitude]`` model/key → parsed JSON."""
    return _llm_call(
        client=InferenceClient(api_key=config.llm.aptitude.model_key),
        model=config.llm.aptitude.model,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=json_object,
        max_tokens_config_key="llm.aptitude.max_tokens",
    )


@traceable(run_type="llm", name="stage3_job_discovery_synthesis")
def job_discovery_llm_call(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float,
    max_tokens: int | None = None,
    json_object: bool = False,
) -> JsonValue:
    """Stage 3 synthesis: ``[llm.job_discovery]`` model/key → parsed JSON."""
    return _llm_call(
        client=InferenceClient(api_key=config.llm.job_discovery.model_key),
        model=config.llm.job_discovery.model,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=json_object,
        max_tokens_config_key="llm.job_discovery.max_tokens",
    )
