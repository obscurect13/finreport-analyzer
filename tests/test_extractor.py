import io
import sys

import pytest
from src.extractor import extract_text_from_pdf

def create_dummy_pdf(text: str) -> bytes:
    """Create a minimal PDF containing the given text using reportlab."""
    from reportlab.pdfgen import canvas
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buffer.getvalue()

def test_basic_extraction():
    pdf_bytes = create_dummy_pdf("Hello PDF")
    extracted = extract_text_from_pdf(pdf_bytes)
    assert "Hello PDF" in extracted

def test_ocr_fallback(monkeypatch):
    pdf_bytes = b"dummy"

    # Return a doc instance that yields no pages (empty iterator) → text stays short
    class FakeDoc:
        def __iter__(self):
            return iter([])

    monkeypatch.setattr("fitz.open", lambda *a, **k: FakeDoc())

    # Mock OCR libraries
    dummy_image = object()
    monkeypatch.setattr("pdf2image.convert_from_bytes", lambda *a, **k: [dummy_image])
    monkeypatch.setattr("pytesseract.image_to_string", lambda img: "OCR text extracted")

    result = extract_text_from_pdf(pdf_bytes)
    assert "OCR text extracted" in result
