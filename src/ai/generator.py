import time
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """\
You are Meera's LinkedIn ghostwriter.

Your job is to take Meera's raw thought and turn it into a postable LinkedIn post while preserving her authentic voice.

The attached voice reference describes how Meera naturally writes.

Do not imitate individual sentences or copy phrases from the reference.

Instead, reproduce the underlying writing characteristics:
- sentence rhythm
- vocabulary
- level of detail
- tone
- way of explaining ideas
- storytelling style
- use of examples
- use of data
- paragraph structure
- degree of directness
- endings
- formatting

The raw note is more important than making the post sound impressive.

Preserve Meera's actual idea and perspective.

Do not invent facts or experiences.

Do not add generic LinkedIn language.

Avoid phrases such as:
'In today's fast-paced world'
'As an entrepreneur'
'Here are 5 lessons'
'I'm excited to share'
'This taught me that'
'Let that sink in'
'The future of...'

Do not add unnecessary emojis or hashtags.

Do not use corporate jargon.

Write like a real founder sharing an observation, not like an AI content writer.

The output must ONLY contain the final LinkedIn post.

No explanation.
No analysis.
No quotation marks around the post.\
"""


def load_voice_reference(voice_file_path: str) -> str:
    path = Path(voice_file_path)
    if not path.exists():
        raise FileNotFoundError(
            f"voice.txt not found at '{voice_file_path}'. "
            "Place voice.txt in the project root or set VOICE_FILE_PATH."
        )
    return path.read_text(encoding="utf-8")


def _build_user_prompt(voice_reference: str, raw_note: str) -> str:
    return f"VOICE REFERENCE:\n{voice_reference}\n\nMEERA'S RAW NOTE:\n{raw_note}"


def _call_anthropic(api_key: str, model: str, user_prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _call_openai(api_key: str, model: str, user_prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _call_gemini(api_key: str, model: str, user_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=4096,
        ),
    )
    # response.text can be None for thinking models; fall back to parts
    if response.text is not None:
        return response.text
    for candidate in response.candidates or []:
        parts = [p.text for p in (candidate.content.parts or []) if p.text]
        if parts:
            return "".join(parts)
    raise ValueError("Gemini returned an empty response")


def generate_linkedin_post(
    raw_note: str,
    voice_file_path: str,
    llm_provider: str,
    llm_api_key: str,
    llm_model: str,
) -> str:
    logger.info("Loading voice reference from '%s'", voice_file_path)
    voice_reference = load_voice_reference(voice_file_path)

    user_prompt = _build_user_prompt(voice_reference, raw_note)

    logger.info("Generation started (provider=%s, model=%s)", llm_provider, llm_model)
    start = time.monotonic()

    if llm_provider == "anthropic":
        post = _call_anthropic(llm_api_key, llm_model, user_prompt)
    elif llm_provider == "openai":
        post = _call_openai(llm_api_key, llm_model, user_prompt)
    elif llm_provider == "gemini":
        post = _call_gemini(llm_api_key, llm_model, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}")

    duration = time.monotonic() - start
    logger.info("Generation completed in %.2fs", duration)

    return post.strip()
