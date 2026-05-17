import os
import time
import shutil
from collections import defaultdict

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Request,
    Depends,
    Query,
)
from fastapi.security import APIKeyHeader

from src.extractor import extract_text_from_pdf
from src.analyzer import analyze_report
from src.telemetry import log_event

router = APIRouter(prefix="/api", tags=["analysis"])

# ── Auth ─────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Depends(api_key_header)):
    if API_KEY and key != API_KEY:
        raise HTTPException(
            status_code=401, detail="Invalid or missing API key."
        )
    return key


# ── Rate limiting (in-memory, per IP) ────────────────────────────────────────
# Rate limit will be read per request to allow tests to modify the env

_request_log: dict[str, list[float]] = defaultdict(list)


def rate_limit(request: Request):
    ip = request.client.host
    now = time.time()
    window = 60.0
    # Determine limit dynamically (default high to avoid test interference)
    env_limit = os.getenv("RATE_LIMIT_PER_MINUTE")
    try:
        limit = int(env_limit) if env_limit and env_limit.strip() else 1000
    except ValueError:
        limit = 1000
    _request_log[ip] = [t for t in _request_log[ip] if now - t < window]
    if len(_request_log[ip]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit} requests per minute.",
        )
    _request_log[ip].append(now)


# ── Routes ───────────────────────────────────────────────────────────────────
@router.post(
    "/analyze", dependencies=[Depends(require_api_key), Depends(rate_limit)]
)
async def analyze(file: UploadFile = File(...), language: str = Query("en")):
    """Upload a PDF report and receive a structured financial analysis."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported."
        )

    file_bytes = await file.read()
    text = extract_text_from_pdf(file_bytes)

    if len(text.strip()) < 200:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract enough text from this PDF, even after "
                "attempting OCR. The file may be corrupted, "
                "password-protected, or an unsupported image format."
            ),
        )

    result = analyze_report(text, language=language, filename=file.filename)
    log_event(
        "analysis_completed",
        filename=file.filename,
        language=language,
        kpi_count=len(result.get("kpis", [])),
        tone=result.get("ton", ""),
    )
    return result


@router.post(
    "/compare", dependencies=[Depends(require_api_key), Depends(rate_limit)]
)
async def compare(
    file1: UploadFile = File(...), file2: UploadFile = File(...),
    language: str = Query("en")
):
    """Upload two PDFs and receive a side-by-side analysis comparison."""
    for f in (file1, file2):
        if not f.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="Both files must be PDFs."
            )

    text1 = extract_text_from_pdf(await file1.read())
    text2 = extract_text_from_pdf(await file2.read())

    for fname, text in ((file1.filename, text1), (file2.filename, text2)):
        if len(text.strip()) < 200:
            raise HTTPException(
                status_code=422,
                detail=f"Could not extract enough text from '{fname}', "
                       "even after attempting OCR.",
            )

    result1 = analyze_report(text1, language=language,
                             use_cache=True, filename=file1.filename)
    result2 = analyze_report(text2, language=language,
                             use_cache=True, filename=file2.filename)

    kpis1 = {k.get("nom"): k for k in result1.get("kpis", [])}
    kpis2 = {k.get("nom"): k for k in result2.get("kpis", [])}
    diffs = []
    for name, k1 in kpis1.items():
        k2 = kpis2.get(name)
        if not k2:
            diffs.append({"kpi": name, "status": "only in first"})
        elif k1.get("valeur") != k2.get("valeur"):
            diffs.append(
                {
                    "kpi": name,
                    "first": k1.get("valeur"),
                    "second": k2.get("valeur"),
                }
            )
    for name in kpis2.keys() - kpis1.keys():
        diffs.append({"kpi": name, "status": "only in second"})

    return {"first": result1, "second": result2, "kpi_differences": diffs}


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/ocr")
async def health_ocr():
    try:
        import pdf2image  # noqa: F401
        import pytesseract  # noqa: F401
    except Exception as e:
        return {"ocr": "error", "detail": str(e)}
    poppler = shutil.which("pdftoppm")
    tesseract = shutil.which("tesseract")
    if not poppler or not tesseract:
        missing = []
        if not poppler:
            missing.append("pdftoppm (poppler)")
        if not tesseract:
            missing.append("tesseract")
        return {"ocr": "missing", "missing": missing}
    return {"ocr": "ok"}


@router.post("/extract", dependencies=[Depends(require_api_key),
                                       Depends(rate_limit)])
async def extract(file: UploadFile = File(...)):
    """Extract raw text from an uploaded PDF file."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400,
                            detail="Only PDF files are supported.")
    file_bytes = await file.read()
    text = extract_text_from_pdf(file_bytes)
    return {"text": text}


@router.get("/validate_env")
def validate_env_endpoint():
    """Run the project's environment validation and report status."""
    from src.config import validate_env
    try:
        validate_env()
        return {"status": "ok"}
    except SystemExit as e:
        return {"status": "error", "detail": str(e)}
