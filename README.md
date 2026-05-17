# 📊 Financial Report Analyzer

A web application that **extracts, analyzes, and compares** annual financial report PDFs using Claude. You can upload a single PDF to get a structured analysis (executive summary, KPIs, tone, themes, risks/opportunities) or upload two PDFs to see a side‑by‑side comparison of their key metrics.
## Project Architecture

The application is composed of several loosely‑coupled components:

- **Streamlit UI** (`app/streamlit_app.py` & `app/components.py`)
  - Handles file uploads, language selection, and displays analysis results.
  - Uses a two‑column layout for side‑by‑side PDF comparison.
- **FastAPI backend** (`api/main.py`, `api/routes.py`)
  - Provides `/api/analyze` and `/api/compare` endpoints.
  - Enforces optional API‑key authentication and per‑IP rate‑limiting.
  - Health checks (`/api/health`, `/api/health/ocr`).
- **Core analysis logic** (`src/`)
  - `extractor.py`: PDF text extraction with OCR fallback.
  - `analyzer.py`: Builds Claude prompt, streams response, parses JSON, and caches results.
  - `cache.py`: SHA‑256‑based on‑text‑and‑language cache (persisted on disk).
  - `telemetry.py`: Logs each analysis request (file name, language, KPI count, tone).
  - `export_formats.py`: Generates CSV/JSON exports.
- **Docker & Compose**
  - Single image builds both UI and API; `docker-compose.yml` runs them as separate containers (`finreport_app` on 8501, `finreport_api` on 8000).
  - Environment variables (`ANTHROPIC_API_KEY`, `API_KEY`, `RATE_LIMIT_PER_MINUTE`) control external services and security.
- **Testing**
  - Unit & integration tests under `tests/` covering extraction, analysis (including caching), API auth/rate‑limit, and the compare endpoint.

This architecture keeps the UI thin, delegates heavy work (Claude calls, OCR) to the backend, and isolates state via caching and telemetry for observability.

## Project Structure
```
finreport-reader/
├── src/                    # Core business logic
│   ├── __init__.py
│   ├── extractor.py        # PDF extraction + OCR fallback
│   ├── analyzer.py         # Claude prompt + streaming response
│   ├── cache.py            # Simple SHA‑256 cache on disk
│   ├── telemetry.py        # Event logging
│   └── export_formats.py   # CSV & JSON export helpers
├── app/                    # Streamlit UI
│   ├── __init__.py
│   ├── components.py       # Reusable UI components
│   └── streamlit_app.py   # Entry point (single‑page layout)
├── api/                    # FastAPI service
│   ├── __init__.py
│   ├── main.py             # FastAPI app with CORS middleware
│   └── routes.py           # Endpoints: analyze, compare, health, auth, rate‑limit
├── Dockerfile               # Builds both UI and API
├── docker-compose.yml       # Multi‑container orchestration
├── requirements.txt
├── README.md
└── tests/                  # Automated test suite
```
```
finreport-reader/
├── src/                    # Core business logic
│   ├── __init__.py
│   ├── extractor.py        # PDF text extraction (PyMuPDF) with OCR fallback
│   ├── analyzer.py         # Claude API call and response parsing
│   ├── cache.py            # Simple SHA‑256 based result cache
│   └── export_formats.py   # CSV & JSON export helpers
│
├── app/                    # Streamlit UI
│   ├── __init__.py
│   ├── components.py       # Reusable UI components
│   └── pages/
│       ├── __init__.py
│       ├── home.py          # Main analysis page
│       └── compare.py       # Side‑by‑side comparison page
│
├── api/                    # FastAPI REST service
│   ├── __init__.py
│   ├── main.py             # FastAPI app with CORS middleware
│   └── routes.py           # /api/analyze, /api/health, /api/health/ocr, /api/compare
│
├── Dockerfile               # Builds both API and UI in a single image
├── docker-compose.yml       # Multi‑container setup (API + Streamlit UI)
├── requirements.txt
└── README.md
```

## Installation (local development)
```bash
# Clone the repo and install Python dependencies
pip install -r requirements.txt

# Set your Claude API key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running locally
### Streamlit UI
```bash
streamlit run app/streamlit_app.py
```
Open http://localhost:8501 in your browser.

### FastAPI backend
```bash
uvicorn api.main:app --reload
```
Open http://localhost:8000/docs for the OpenAPI UI.

## Docker deployment
```bash
# Build and start both services (API on 8000, UI on 8501)
docker compose up --build -d
```
The UI will be reachable at http://localhost:8501 and the API at http://localhost:8000.

To stop and clean up:
```bash
docker compose down
```

## API Endpoints
| Method | Route | Description |
|--------|-------|-------------|
| POST   | `/api/analyze` | Upload a PDF and receive a structured JSON analysis |
| GET    | `/api/health` | Simple health check |
| GET    | `/api/health/ocr` | Verify OCR dependencies (`pdf2image` & `tesseract`) |
| POST   | `/api/compare` | Upload two PDFs and get a side‑by‑side comparison and KPI diff |

## Export Formats
From the UI you can download the analysis as:
* **PDF** – styled report (default)
* **CSV** – table of KPIs and summary fields
* **JSON** – raw structured data

## Caching
The backend caches Claude responses keyed by a SHA‑256 hash of the extracted text and selected language. Re‑analyzing the same document returns instantly without additional Claude calls, saving quota and latency.

---
*Built with Streamlit, FastAPI, Claude API, and a little OCR magic.*