from openai import OpenAI

from app.validate import parse_json_response


def call_stage(
    api_key: str,
    system_prompt: str,
    user_message: str,
    model: str = "gpt-4o",
) -> object:
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.3,
        response_format={"type": "json_object"},
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
    api_key: str,
    system_prompt: str,
    user_message: str,
    model: str = "gpt-4o",
) -> str:
    """Stage 2 verified discovery — markdown/TSV, not JSON."""
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM")
    return content.strip()
