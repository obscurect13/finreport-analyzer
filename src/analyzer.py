import re
import json
import anthropic
from dotenv import load_dotenv
load_dotenv()


def _build_prompt(text: str, language: str) -> str:
    """Construct the prompt sent to Claude based on language."""
    if language.lower().startswith("es"):
        intro = (
            "Eres un analista financiero senior."
            "Analiza este informe financiero y devuelve "
            "SÓLO un objeto JSON válido "
            "(sin markdown, sin backticks)"
            "con esta estructura exacta:"
        )
    else:
        intro = (
            "You are a senior financial analyst."
            "Analyze this financial report and return "
            "ONLY a valid JSON object"
            "(no markdown, no backticks)"
            "with this exact structure:"
        )
    schema = "{\n"
    schema += '  "resume": "Executive summary in 3-4 sentences",\n'
    schema += '  "ton": "optimiste" | "neutre" | "pessimiste",\n'
    schema += (
        '  "raison_ton": "Short explanation of the tone in 1 sentence",\n'
    )
    schema += '  "kpis": [\n'
    schema += '    {"nom": "KPI name", "valeur": "Value with unit"'
    schema += ', "variation": "+X%" | "-X%" | "N/A"'
    schema += ', "sens": "pos" | "neg" | "neu"}\n'
    schema += "  ],\n"
    schema += '  "themes": ["theme1", "theme2", "theme3"],\n'
    schema += '  "risques": ["risk1", "risk2"],\n'
    schema += '  "opportunites": ["opportunity1", "opportunity2"]\n'
    schema += "}\n"
    prompt_body = (
                f"{intro}\n{schema}"
                "\nExtract up to 6 key financial KPIs"
                "(revenue, net income, EBITDA, margin, debt, growth...)."
                "\nIdentify 4-6 major strategic themes."
                "\nList 2-3 risks and 2-3 opportunities."
                "\n\nReport to analyze:\n"
                f"{text}"
                )
    return prompt_body


def _parse_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON. Raises ValueError on failure."""
    raw = raw.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw}"
        )


def analyze_report(
    text: str, language: str = "en", use_cache: bool = True, filename: str = ""
) -> dict:
    """Send extracted report text to Claude and return a structured dict.
    Falls back to cache before calling the API.
    """
    from .cache import make_key, get_cached_result, set_cached_result

    cache_key = make_key(text, language, filename)
    if use_cache:
        cached = get_cached_result(cache_key)
        if cached:
            return cached

    client = anthropic.Anthropic()
    prompt = _build_prompt(text, language)

    # Streaming response
    raw = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text_chunk in stream.text_stream:
            raw += text_chunk

    result = _parse_response(raw)
    if use_cache:
        set_cached_result(cache_key, result)
    return result
