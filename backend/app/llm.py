from huggingface_hub import InferenceClient

from app.config import config
from app.validate import parse_json_response


def _client() -> InferenceClient:
    return InferenceClient(api_key=config.llm.aptitude_model_key)


def complete_chat_json(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> object:
    """Hugging Face chat completion; returns parsed JSON."""
    completion = _client().chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        model=model or config.llm.aptitude_model,
        temperature=config.llm.temperature,
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
    """Hugging Face chat completion returning plain text."""
    completion = _client().chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        model=model or config.llm.aptitude_model,
        temperature=config.llm.temperature,
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    return content.strip()
