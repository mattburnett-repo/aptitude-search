# Aptitude Search — MVP Web

Single-page UI for the two-stage pipeline (resume → aptitude profile → verified matches).

Hugging Face credentials are configured on the API server in `backend/config.toml` (`[llm.aptitude]` for Stage 1; `[llm.job_discovery]` for Stage 2). The browser does not send API keys.

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
- **Run pipeline (1 → 2)** — single request; shows stage 1 and stage 2 JSON in expandable panels.
- **Export JSON** — downloads `{ aptitude_profile, verified_matches }`.
- **Copy verified matches** — copies `verified_matches` JSON to clipboard.

There is no refine/iterate panel. Stage 2 (job search) runs automatically with the pipeline; see `docs/PROMPT-CONTRACT.md`.

## Build

```bash
npm run build
```

Deploy `dist/` to Vercel/Netlify. Point the browser at your API (today: dev proxy only; add `VITE_API_URL` or reverse-proxy `/api` in production if you deploy API separately).
