import json
import pytest
from unittest.mock import MagicMock, patch
from src.analyzer import analyze_report, _parse_response


# ── _parse_response ───────────────────────────────────────────────────────────

def test_parse_response_valid():
    raw = json.dumps({"ton": "neutre", "resume": "ok"})
    result = _parse_response(raw)
    assert result["ton"] == "neutre"


def test_parse_response_strips_markdown_fences():
    raw = "```json\n{\"ton\": \"optimiste\"}\n```"
    result = _parse_response(raw)
    assert result["ton"] == "optimiste"


def test_parse_response_invalid_json_raises():
    with pytest.raises(ValueError, match="invalid JSON"):
        _parse_response("not json at all")


# ── analyze_report (streaming mock) ──────────────────────────────────────────

DUMMY_RESULT = {
    "resume": "Summary",
    "ton": "neutre",
    "raison_ton": "Neutral tone",
    "kpis": [],
    "themes": [],
    "risques": [],
    "opportunites": [],
}


def _make_stream_mock(text: str):
    """Build a mock that mimics anthropic's streaming context manager."""
    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter([text])
    return stream


@patch("src.analyzer.anthropic.Anthropic")
def test_analyze_report_returns_dict(mock_anthropic, tmp_path, monkeypatch):
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))
    client = MagicMock()
    client.messages.stream.return_value = _make_stream_mock(json.dumps(DUMMY_RESULT))
    mock_anthropic.return_value = client

    result = analyze_report("some report text", language="en")
    assert isinstance(result, dict)
    assert result["ton"] == "neutre"


@patch("src.analyzer.anthropic.Anthropic")
def test_analyze_report_uses_cache(mock_anthropic, tmp_path, monkeypatch):
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))
    client = MagicMock()
    client.messages.stream.return_value = _make_stream_mock(json.dumps(DUMMY_RESULT))
    mock_anthropic.return_value = client

    # First call hits API
    analyze_report("cached text", language="en")
    assert client.messages.stream.call_count == 1

    # Second call should use cache, not call API again
    analyze_report("cached text", language="en")
    assert client.messages.stream.call_count == 1


@patch("src.analyzer.anthropic.Anthropic")
def test_analyze_report_invalid_json_raises(mock_anthropic, tmp_path, monkeypatch):
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))
    client = MagicMock()
    client.messages.stream.return_value = _make_stream_mock("this is not json")
    mock_anthropic.return_value = client

    with pytest.raises(ValueError, match="invalid JSON"):
        analyze_report("bad response text", language="en")
