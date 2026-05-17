# Aptitude Search — MVP Web

Single-page UI for the two-stage pipeline (resume → aptitude profile → verified matches).

**API key** is stored in `localStorage` only (`aptitude-search-openai-key`). It is sent to your API instance as `X-OpenAI-Api-Key` on each request—not to any third-party server beyond OpenAI via your backend.

**Model** is also stored in `localStorage` (`aptitude-search-openai-model`, default `gpt-4o`).

## Run

Terminal 1 — API:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
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
