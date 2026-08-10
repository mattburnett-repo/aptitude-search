# Shot list

Record in order. Prefer the **frontend UI**; Swagger is optional B-roll for a technical cut.

## Prep (before record)

1. API running (`uvicorn` on port **3001** — see `backend/README.md`).
2. Frontend running and pointed at that API.
3. Use the sample resume from `fixtures/pipeline-request-example.json` (or paste the same text into the UI).
4. Constraints ready: Toronto, remote, salary ≥ 110000, SaaS/FinTech include, Gambling exclude.
5. Browser zoom **100%**, dark/light theme: pick one and stick with it (light matches stills).
6. Hide bookmarks bar; use a clean window or full-screen.

## Primary path (product demo)

| Shot | Duration | Scene | Action | Notes |
|------|----------|-------|--------|-------|
| A | 4s | Title still | Import `stills/title-card.png` | Hold; fade to UI |
| B | 8s | Start / input | Show hero + paste resume into field | Cursor visible; no typing typos |
| C | 6s | Criteria | Open constraints; set location/remote/industries | Keep motion calm |
| D | 4s | Run | Click primary run / pipeline CTA | Hold on button press |
| E | 8s | Progress → Profile | Show running label, then Profile stage | Skip long waits in edit; jump-cut if pipeline is slow |
| F | 4s | Roles | Brief Role family / Matches view | One scroll only |
| G | 4s | Beat still | Cut to `stills/beat-three-stages.png` | Optional if timeline is tight |
| H | 10s | Jobs | Verified matches: scroll 1–2 jobs; click one posting URL | Emphasize real links |
| I | 5s | End still | `stills/end-card.png` | Hold for CTA |

**Total roll:** ~50–60s raw → trim to ~45s.

## Optional B-roll (engineers / API cut)

| Shot | Scene | Action |
|------|-------|--------|
| S1 | Swagger `http://localhost:3001/docs` | Expand `POST /v1/pipeline` |
| S2 | Try it out | Load example body (fixture) → Execute |
| S3 | Response | Scroll `verified_matches` in JSON | Do not stay >5s |

Use S1–S3 only if you cut a second “API” version; the main demo stays on the UI.

## Do not film

- Raw `.env` / `config.toml` with keys
- Failed runs / error toasts as the hero path
- Long uncut waits; jump-cut or speed-ramp instead
