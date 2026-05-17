# 📊 Financial Report Analyzer

A web application that **extracts, analyzes, and compares** annual financial report PDFs using Claude. Upload a single PDF to get a structured analysis (executive summary, KPIs, tone, themes, risks/opportunities), or upload two PDFs for a side-by-side comparison of their key metrics.

## Project Architecture

The application is composed of several loosely-coupled components:

- **Streamlit UI** (`app/streamlit_app.py` & `app/components.py`)
  - Handles file uploads, language selection, and displays analysis results.
  - Calls `/api/analyze` or `/api/compare` directly — no client-side pre-extraction.
  - `app/_pages/compare.py` provides the side-by-side comparison page.
- **FastAPI backend** (`api/main.py`, `api/routes.py`)
  - Provides `/api/analyze`, `/api/compare`, and `/api/extract` endpoints.
  - Enforces optional API-key authentication and per-IP rate-limiting.
  - Raises `422` with a clear message if a PDF yields too little text even after OCR.
  - Health checks at `/api/health` and `/api/health/ocr`.
- **Core analysis logic** (`src/`)
  - `extractor.py`: Native PDF text extraction via PyMuPDF; falls back to Tesseract OCR for scanned/image-only documents.
  - `analyzer.py`: Builds the Claude prompt, streams the response, parses JSON, and caches results.
  - `cache.py`: SHA-256 cache keyed on extracted text, language, **and filename** — preventing collisions when different files share identical content.
  - `telemetry.py`: Logs each analysis request (filename, language, KPI count, tone).
  - `export_formats.py`: Generates CSV/JSON exports.
  - `exporter.py`: Generates the styled PDF report.
  - `config.py`: Validates required environment variables at startup.
- **Docker & Compose**
  - Single `Dockerfile` builds one image used by both services.
  - `docker-compose.yml` runs two containers (`finreport_api` on 8000, `finreport_app` on 8501).
  - The `app` service depends on `api` via a healthcheck — it won't start until the API is ready.
  - `API_BASE_URL=http://api:8000` is set automatically inside Docker so containers can reach each other.
- **Environment**
  - `.env` — stores local secrets (`ANTHROPIC_API_KEY`, `API_KEY`, `RATE_LIMIT_PER_MINUTE`).
  - `python-dotenv` loads `.env` automatically in local development.
- **Testing**
  - Unit & integration tests under `tests/` covering extraction, analysis (including caching), API auth/rate-limit, and the compare endpoint.

## Project Structure

```
finreport-analyzer/
├── src/                    # Core business logic
│   ├── __init__.py
│   ├── extractor.py        # PDF extraction + OCR fallback
│   ├── analyzer.py         # Claude prompt + streaming response, caching
│   ├── cache.py            # SHA‑256 based cache on disk
│   ├── telemetry.py        # Event logging
│   ├── export_formats.py   # CSV & JSON export helpers
│   ├── exporter.py         # PDF report generation (styled)
│   └── config.py          # Application configuration (if needed)
├── app/                    # Streamlit UI
│   ├── __init__.py
│   ├── components.py       # Reusable UI components
│   ├── streamlit_app.py   # Entry point (single‑page layout with comparison)
│   └── _pages/
│       └── compare.py      # Side‑by‑side comparison page
├── api/                    # FastAPI service
│   ├── __init__.py
│   ├── main.py             # FastAPI app with CORS middleware
│   └── routes.py           # Endpoints: analyze, compare, health, auth, rate‑limit
├── Dockerfile               # Builds both UI and API in one image
├── .env                     # Local configuration (API keys, etc.)
├── .gitignore               # Files ignored by version control
├── docker-compose.yml       # Multi‑container orchestration (API + UI)
├── requirements.txt
├── README.md               # Documentation (this file)
└── tests/                  # Automated test suite
    ├── test_analyzer.py
    ├── test_api.py
    ├── test_cache.py
    ├── test_compare.py
    ├── test_config.py
    └── test_extractor.py
```
## Installation (local development)

### Prerequisites

The OCR fallback requires two system packages in addition to the Python dependencies:

**macOS**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils
```

**Windows**
- Tesseract: download the installer from https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: download from https://github.com/oschwartz10612/poppler-windows/releases and add `bin/` to your PATH

### Python dependencies

```bash
pip install -r requirements.txt
```

### Environment file

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
API_KEY=               # optional: enforces X-API-Key auth on all endpoints
RATE_LIMIT_PER_MINUTE= # optional: default is 10
```

## Running locally

The UI talks to the API, so **both must be running**. Open two terminals:

**Terminal 1 — API**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Streamlit UI**
```bash
streamlit run app/streamlit_app.py
```

Open http://localhost:8501 in your browser. The API docs are at http://localhost:8000/docs.

## Docker deployment

```bash
# Build and start both services (API on 8000, UI on 8501)
docker compose up --build
```
If it freeze after building the container then exit and run:

```bash
docker-compose up -d
docker compose up --build
```

The UI is reachable at http://localhost:8501 and the API at http://localhost:8000. The `app` container waits for the `api` healthcheck to pass before starting, so there's no race condition on boot.

```bash
docker compose down   # stop and clean up
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/analyze` | Upload a PDF → structured JSON analysis |
| POST | `/api/compare` | Upload two PDFs → side-by-side comparison + KPI diff |
| POST | `/api/extract` | Upload a PDF → raw extracted text (with OCR fallback) |
| GET  | `/api/health` | Simple health check |
| GET  | `/api/health/ocr` | Verify OCR dependencies (tesseract + poppler) |
| GET  | `/api/validate_env` | Verify required environment variables are set |

All write endpoints require an `X-API-Key` header if `API_KEY` is set in the environment.

## Caching

Claude responses are cached on disk, keyed by a SHA-256 hash of the extracted text, the selected language, and the filename. Re-analyzing the same document returns instantly without additional Claude calls. The cache is stored in the `cache/` directory and persists across restarts.

## Export Formats

From the UI you can download the analysis as:
- **PDF** — styled report
- **CSV** — KPIs and summary fields as a table
- **JSON** — raw structured data

## Running tests

```bash
pytest tests/
```

---
*Built with Streamlit, FastAPI, Claude API, PyMuPDF, and Tesseract OCR.*
