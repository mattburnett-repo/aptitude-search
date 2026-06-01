# Aptitude Search — MVP Web

Single-page UI for the two-stage pipeline (resume → aptitude profile → verified matches).

Hugging Face credentials are configured on the API server in `backend/config.toml` (`[llm].api_key`, `default_model`). The browser does not send an API key.

## Run

Terminal 1 — API:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # if needed; set [llm].api_key
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

Terminal 2 — Web:

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

Vite proxies `/api/*` → `http://localhost:3001/*` (see `vite.config.ts`). The app calls `POST /api/v1/pipeline`.

## UI behavior

- Paste resume; optional constraints (location, remote, salary min, industries include/exclude).
- **Run pipeline (1 → 2)** — single request; shows stage 1 JSON and stage 2 text in expandable panels.
- **Export JSON** — downloads `{ aptitude_profile, verified_matches }`.
- **Copy verified matches** — copies stage 2 text to clipboard.

There is no refine/iterate panel. For best stage-2 verification, run Prompt 2 in Cursor Agent with web search (see repo `docs/`).

## Build

```bash
npm run build
```

Deploy `dist/` to Vercel/Netlify. Point the browser at your API (today: dev proxy only; add `VITE_API_URL` or reverse-proxy `/api` in production if you deploy API separately).
