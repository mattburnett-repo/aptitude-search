from huggingface_hub import InferenceClient
from langsmith import traceable

from app.core.config import config
from app.core.validate import parse_json_response


def _aptitude_client() -> InferenceClient:
    return InferenceClient(api_key=config.llm.aptitude_model_key)


@traceable(run_type="llm", name="stage1_aptitude_profile")
def complete_chat_json(
    system_prompt: str,
    user_message: str,
) -> object:
    """Hugging Face chat completion; returns parsed JSON."""
    completion = _aptitude_client().chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        model=config.llm.aptitude_model,
        temperature=config.llm.temperature,
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    return parse_json_response(content)
