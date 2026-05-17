import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 15000) -> str:
    """Extract text from a PDF byte stream.

    First attempts native text extraction via PyMuPDF. If the result is too
    short (scanned/image-only PDF), falls back to OCR via Tesseract.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        if len(text) >= max_chars:
            break

    if len(text.strip()) >= 200:
        return text[:max_chars]

    # Native extraction yielded too little — attempt OCR fallback
    logger.info(
        "Native extraction returned %d chars; attempting OCR fallback.",
        len(text.strip()),
    )
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(file_bytes, dpi=200)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
            if len(ocr_text) >= max_chars:
                break

        if len(ocr_text.strip()) > len(text.strip()):
            logger.info("OCR fallback succeeded (%d chars).",
                        len(ocr_text.strip()))
            return ocr_text[:max_chars]
        else:
            logger.warning("OCR fallback produced no useful text.")
    except Exception as e:
        logger.error("OCR fallback failed: %s", e)

    return text[:max_chars]
