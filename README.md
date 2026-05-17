# 📊 Financial Report Analyzer

A web application that **extracts, analyzes, and compares** annual financial report PDFs using Claude. You can upload a single PDF to get a structured analysis (executive summary, KPIs, tone, themes, risks/opportunities) or upload two PDFs to see a side‑by‑side comparison of their key metrics.
## Project Architecture

The application is composed of several loosely‑coupled components:

- **Streamlit UI** (`app/streamlit_app.py` & `app/components.py`)
  - Handles file uploads, language selection, and displays analysis results.
  - Uses a two‑column layout for side‑by‑side PDF comparison.
  - `app/_pages/compare.py` provides the side‑by‑side comparison page functionality.
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
  - `exporter.py`: Generates the styled PDF report.
  - `config.py`: Holds optional configuration settings for the application.
- **Docker & Compose**
  - Single image builds both UI and API; `docker-compose.yml` runs them as separate containers (`finreport_app` on 8501, `finreport_api` on 8000).
  - Environment variables (`ANTHROPIC_API_KEY`, `API_KEY`, `RATE_LIMIT_PER_MINUTE`) control external services and security.
- **Environment files**
  - `.env` – stores local configuration such as API keys.
  - `.gitignore` – lists files and directories excluded from version control.
- **Testing**
  - Unit & integration tests under `tests/` covering extraction, analysis (including caching), API auth/rate‑limit, and the compare endpoint.

This architecture keeps the UI thin, delegates heavy work (Claude calls, OCR) to the backend, and isolates state via caching and telemetry for observability.

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