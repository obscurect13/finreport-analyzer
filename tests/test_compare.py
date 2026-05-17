import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

DUMMY_RESULT = {
    "resume": "Summary",
    "ton": "neutre",
    "raison_ton": "Neutral tone",
    "kpis": [{"nom": "Revenue", "valeur": "$10B", "variation": "+5%", "sens": "pos"}],
    "themes": ["Growth"],
    "risques": ["Risk A"],
    "opportunites": ["Opportunity A"],
}


def _make_dummy_pdf() -> bytes:
    from reportlab.pdfgen import canvas
    import io
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "A " * 150)
    c.showPage()
    c.save()
    return buf.getvalue()


def _make_stream_mock(result: dict):
    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter([json.dumps(result)])
    return stream


@patch("src.analyzer.anthropic.Anthropic")
def test_compare_endpoint(mock_anthropic, tmp_path, monkeypatch):
    monkeypatch.setattr("src.cache.CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("API_KEY", "")

    # Return different results for each call
    result_a = {**DUMMY_RESULT, "resume": "Report A summary"}
    result_b = {**DUMMY_RESULT, "resume": "Report B summary", "kpis": [
        {"nom": "Revenue", "valeur": "$12B", "variation": "+8%", "sens": "pos"}
    ]}

    mock_anthropic.return_value.messages.stream.side_effect = [
        _make_stream_mock(result_a),
        _make_stream_mock(result_b),
    ]

    pdf1 = _make_dummy_pdf()
    pdf2 = _make_dummy_pdf()

    r = client.post(
        "/api/compare",
        files=[
            ("file1", ("a.pdf", pdf1, "application/pdf")),
            ("file2", ("b.pdf", pdf2, "application/pdf")),
        ],
    )

    assert r.status_code == 200
    data = r.json()
    assert "first" in data and "second" in data
    assert data["first"]["resume"] == "Report A summary"
    assert data["second"]["resume"] == "Report B summary"
    assert "kpi_differences" in data
    # Revenue values differ → should appear in diff
    diff_names = [d["kpi"] for d in data["kpi_differences"]]
    assert "Revenue" in diff_names


def test_compare_rejects_non_pdf(monkeypatch):
    monkeypatch.setenv("API_KEY", "")
    r = client.post(
        "/api/compare",
        files=[
            ("file1", ("a.txt", b"text content", "text/plain")),
            ("file2", ("b.pdf", b"pdf content", "application/pdf")),
        ],
    )
    assert r.status_code == 400
