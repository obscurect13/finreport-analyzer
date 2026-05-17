import os
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

DUMMY_RESULT = {
    "resume": "Summary",
    "ton": "neutre",
    "raison_ton": "Neutral tone",
    "kpis": [],
    "themes": [],
    "risques": [],
    "opportunites": [],
}


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_ocr():
    r = client.get("/api/health/ocr")
    assert r.status_code == 200
    assert r.json()["ocr"] in {"ok", "missing", "error"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_analyze_requires_api_key_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("API_KEY", "secret")
    # Reload routes so the new env var is picked up
    import importlib, api.routes
    importlib.reload(api.routes)

    dummy_pdf = _make_dummy_pdf()
    r = client.post("/api/analyze", files={"file": ("test.pdf", dummy_pdf, "application/pdf")})
    assert r.status_code == 401


def test_analyze_accepts_valid_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))

    import importlib, api.routes
    importlib.reload(api.routes)

    with patch("src.analyzer.anthropic.Anthropic") as mock_anthropic:
        stream = MagicMock()
        stream.__enter__ = MagicMock(return_value=stream)
        stream.__exit__ = MagicMock(return_value=False)
        stream.text_stream = iter([json.dumps(DUMMY_RESULT)])
        mock_anthropic.return_value.messages.stream.return_value = stream

        dummy_pdf = _make_dummy_pdf(long=True)
        r = client.post(
            "/api/analyze",
            files={"file": ("test.pdf", dummy_pdf, "application/pdf")},
            headers={"X-API-Key": "secret"},
        )
    assert r.status_code == 200


# ── Rate limiting ─────────────────────────────────────────────────────────────

def test_rate_limit_returns_429(monkeypatch, tmp_path):
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))

    import importlib, api.routes
    importlib.reload(api.routes)
    # Clear the rate limit log
    api.routes._request_log.clear()

    with patch("src.analyzer.anthropic.Anthropic") as mock_anthropic:
        stream = MagicMock()
        stream.__enter__ = MagicMock(return_value=stream)
        stream.__exit__ = MagicMock(return_value=False)
        stream.text_stream = iter([json.dumps(DUMMY_RESULT)])
        mock_anthropic.return_value.messages.stream.return_value = stream

        dummy_pdf = _make_dummy_pdf(long=True)

        for _ in range(2):
            client.post("/api/analyze", files={"file": ("test.pdf", dummy_pdf, "application/pdf")})
            # reset stream iterator for next call
            stream.text_stream = iter([json.dumps(DUMMY_RESULT)])

        r = client.post("/api/analyze", files={"file": ("test.pdf", dummy_pdf, "application/pdf")})

    assert r.status_code == 429


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_dummy_pdf(long: bool = False) -> bytes:
    from reportlab.pdfgen import canvas
    import io
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    text = ("A " * 150) if long else "short"
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()
