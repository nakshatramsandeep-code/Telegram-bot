import json

from src.utils.logger import get_logger

logger = get_logger(__name__)

SCORING_PROMPT = """\
You are evaluating a raw note from Meera, the founder of Skinstinct (a skincare brand in India), \
to decide if it is worth turning into a LinkedIn post.

Score the note from 0 to 10 based on these 5 dimensions (2 points each):

1. Specificity (0-2): Does it contain a concrete observation, number, or example — or is it too vague?
2. Insight / Originality (0-2): Does it offer a non-obvious perspective — or is it generic?
3. Narrative potential (0-2): Is there a story, conflict, or journey — or just a fragment of a thought?
4. Audience relevance (0-2): Will founders, skincare professionals, or D2C builders find genuine value in this?
5. Post-worthiness (0-2): Is there enough material for a full LinkedIn post — or is it too thin?

Respond ONLY with a JSON object in this exact format:
{"score": <integer 0-10>, "reason": "<one sentence explaining the score>"}

No explanation outside the JSON. No markdown fences. Just the JSON object.\
"""


def score_note(
    raw_note: str,
    llm_provider: str,
    llm_api_key: str,
    llm_model: str,
) -> tuple[int, str]:
    """Score a raw note 0-10. Returns (score, reason)."""
    logger.info("Scoring note (provider=%s, model=%s)", llm_provider, llm_model)

    if llm_provider == "anthropic":
        text = _call_anthropic(llm_api_key, llm_model, raw_note)
    elif llm_provider == "openai":
        text = _call_openai(llm_api_key, llm_model, raw_note)
    elif llm_provider == "gemini":
        text = _call_gemini(llm_api_key, llm_model, raw_note)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {llm_provider}")

    # Strip markdown fences if model adds them anyway
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    data = json.loads(text)
    score = max(0, min(10, int(data["score"])))
    reason = str(data["reason"])

    logger.info("Note scored %d/10: %s", score, reason)
    return score, reason


def _call_anthropic(api_key: str, model: str, raw_note: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=512,
        system=SCORING_PROMPT,
        messages=[{"role": "user", "content": raw_note}],
    )
    return message.content[0].text


def _call_openai(api_key: str, model: str, raw_note: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCORING_PROMPT},
            {"role": "user", "content": raw_note},
        ],
        max_tokens=512,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _call_gemini(api_key: str, model: str, raw_note: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=raw_note,
        config=types.GenerateContentConfig(
            system_instruction=SCORING_PROMPT,
            max_output_tokens=2048,
        ),
    )
    if response.text is not None:
        return response.text
    for candidate in response.candidates or []:
        parts = [p.text for p in (candidate.content.parts or []) if p.text]
        if parts:
            return "".join(parts)
    raise ValueError("Gemini returned an empty response for scoring")
