# aptitude-search

A multi-stage LLM pipeline for aptitude-driven job search, career targeting, and search strategy generation.

## Status

**Phase 1:** Prompt workflow pack — run manually in ChatGPT, Claude, or similar ([docs/WORKFLOW.md](docs/WORKFLOW.md)).

**Phase 2:** Python/FastAPI orchestration API + Vite/React web UI (BYO OpenAI API key).

## Quick start (prompt pack only)

1. Read [docs/WORKFLOW.md](docs/WORKFLOW.md) for the 10-minute walkthrough.
2. Run prompts in order under `prompts/` (1 → 2 → 3; use 4 to refine).
3. Validate outputs against `schemas/`.

## Running the API and web app

Use **two terminals**. The web UI proxies API requests to port **3001**.

### 1. API (Python / FastAPI)

First-time setup:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start the server (from `backend/` — use the venv’s Python, not global `uvicorn`):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

Health check: http://localhost:3001/health

Optional — validate golden fixtures:

```bash
.venv/bin/python scripts/validate_fixtures.py
```

More detail: [backend/README.md](backend/README.md)

### 2. Web (Vite + React)

First-time setup:

```bash
cd frontend
npm install
```

Start the dev server:

```bash
npm run dev
```

Open http://localhost:5173 — paste your **OpenAI API key** in the UI (stored in the browser only). The app sends it to the local API as `X-OpenAI-Api-Key`.

More detail: [frontend/README.md](frontend/README.md)

## Repository layout

```
prompts/          # Stage prompts (copy-paste ready)
schemas/          # JSON Schema for each stage output
fixtures/         # Sample resumes and golden example outputs
docs/             # WORKFLOW, PROMPT-CONTRACT, TESTING
design-docs/      # Product thesis and architecture notes
backend/          # Orchestration API — Python/FastAPI (Phase 2)
frontend/         # MVP frontend (Phase 2)
```

## Design docs

See [design-docs/](design-docs/) for concept, thesis, and monetization notes.

## Plan

Authoritative build plan: [.cursor/plans/aptitude-search-build.plan.md](.cursor/plans/aptitude-search-build.plan.md)
