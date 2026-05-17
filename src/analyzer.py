import re
import json
import anthropic


def _build_prompt(text: str, language: str) -> str:
    if language.lower().startswith("es"):
        intro = "Eres un analista financiero senior. Analiza este informe financiero y devuelve SÓLO un objeto JSON válido (sin markdown, sin backticks) con esta estructura exacta:"
    else:
        intro = "You are a senior financial analyst. Analyze this financial report and return ONLY a valid JSON object (no markdown, no backticks) with this exact structure:"

    return f"""{intro}
{{
  "resume": "Executive summary in 3-4 sentences",
  "ton": "optimiste" | "neutre" | "pessimiste",
  "raison_ton": "Short explanation of the tone in 1 sentence",
  "kpis": [
    {{"nom": "KPI name", "valeur": "Value with unit", "variation": "+X%" or "-X%" or "N/A", "sens": "pos" | "neg" | "neu"}}
  ],
  "themes": ["theme1", "theme2", "theme3"],
  "risques": ["risk1", "risk2"],
  "opportunites": ["opportunity1", "opportunity2"]
}}

Extract up to 6 key financial KPIs (revenue, net income, EBITDA, margin, debt, growth...).
Identify 4-6 major strategic themes.
List 2-3 risks and 2-3 opportunities.

Report to analyze:
{text}"""


def _parse_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON. Raises ValueError on failure."""
    raw = raw.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\n\nRaw response:\n{raw}")


def analyze_report(text: str, language: str = "en", use_cache: bool = True) -> dict:
    """
    Send extracted report text to Claude using streaming and return a structured dict.
    Falls back to cache before calling the API.
    """
    from .cache import make_key, get_cached_result, set_cached_result
    cache_key = make_key(text, language)
    if use_cache:
        cached = get_cached_result(cache_key)
        if cached:
            return cached

    client = anthropic.Anthropic()
    prompt = _build_prompt(text, language)

    # ── Streaming ──────────────────────────────────────────────────────────
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
