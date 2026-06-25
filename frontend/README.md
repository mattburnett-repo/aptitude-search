# Aptitude Search — MVP Web

Single-page UI for the three-stage pipeline (resume → aptitude profile → role family plan → verified matches).

Hugging Face credentials are configured on the API server in `backend/config.toml` (`[llm.aptitude].model_key` for LLM calls in Stage 1, Stage 2, and Stage 3 synthesis). Stage 3 discovery uses web search only (`[llm.job_discovery]` sets search/scrape limits and synthesis temperature). The browser does not send API keys.

## Run

Terminal 1 — API:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # if needed; set [llm.aptitude].model_key
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

Terminal 2 — Web:

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

Vite proxies `/api/*` → `http://localhost:3001/*` (see `vite.config.ts`). The app calls `POST /api/v1/pipeline`.

If pipeline progress updates lag in the UI, set `VITE_API_URL=http://localhost:3001` in `frontend/.env.local` to bypass the dev proxy (restart `npm run dev`).

## UI behavior

- Paste resume; optional constraints (location, remote, salary min, industries include/exclude).
- **Run pipeline (1 → 2 → 3)** — single request; shows Stage 1 and Stage 3 JSON in expandable panels.
- **Save as PDF** — on the aptitude profile and verified matches panels; opens formatted PDFs in new browser tabs (panel content only; Raw JSON is excluded).

There is no refine/iterate panel. Stage 3 (job search) runs automatically with the pipeline; see `docs/PROMPT-CONTRACT.md`.

## Build

```bash
npm run build
```

Deploy `dist/` to Vercel/Netlify. Point the browser at your API (today: dev proxy only; add `VITE_API_URL` or reverse-proxy `/api` in production if you deploy API separately).
