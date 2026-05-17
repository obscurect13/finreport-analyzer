import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 15000) -> str:
    """Extract raw text from a PDF; fall back to OCR if needed."""
    """Extract raw text from a PDF byte stream, up to max_chars."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        if len(text) > max_chars:
            break
    # If extracted text is too short, try OCR fallback
    if len(text.strip()) < 200:
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            images = convert_from_bytes(file_bytes)
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img)
                if len(ocr_text) > max_chars:
                    break
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
        except Exception:
            # If OCR fails, keep original text
            pass
    return text[:max_chars]
