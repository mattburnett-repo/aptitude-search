# Aptitude Search — MVP Web

Single-page UI for the pipeline. **API key is stored in `localStorage` only** (never sent to our server except as `X-OpenAI-Api-Key` to your own API instance).

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

## Build

```bash
npm run build
```

Deploy `dist/` to Vercel/Netlify; set API proxy or `VITE_API_URL` if you add env support later.
