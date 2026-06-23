# Aptitude Search — Workflow Guide

**Product workflow:** [Stage 1](../prompts/01-resume-to-aptitude-profile.md) → Stage 2 ([discovery](../docs/PROMPT-CONTRACT.md) + [synthesis](../prompts/03-job-discovery-synthesis.md))

**Run pipeline:** [backend/README.md](../backend/README.md) (Swagger at `/docs`)

`XX-original-aptitude-prompt.md` is the reference spec used to build Prompts 1 and 2.

---

## Resume source

**Demo:** `fixtures/sample-resumes/career-changer-mixed-stack.txt` (also `marketing-operations-lead.txt`, `senior-backend-engineer.txt`)

**Your resume:** `resume-text.txt` at repo root (gitignored)

---

## Prompt 1 — Aptitude profile

See [prompts/README.md](../prompts/README.md). Output: JSON only, conforming to `schemas/aptitude-profile.schema.json`.

## Stage 2 — Verified job discovery

See [prompts/README.md](../prompts/README.md). Input: Stage 1 JSON plus optional constraints (`schemas/constraints.schema.json`).

The API runs two phases:

1. **Discovery** — Python builds queries from profile + constraints, runs `search_job_postings` — collects `found_jobs`.
2. **Synthesis** (`03-job-discovery-synthesis.md`) — maps `found_jobs` into schema-strict JSON with `search_plan`, `results`, and `notes` per `schemas/job-discovery-results.schema.json`.

Configure **`[job_discovery].discovery_query_max`** in `backend/config.toml`. Details: [PROMPT-CONTRACT](PROMPT-CONTRACT.md).

**API:** `POST /v1/pipeline` runs Stage 1 then Stage 2 with no manual step. Use Swagger at `http://localhost:3001/docs`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).

---

## Optional: API + web UI

- **API:** [backend/README.md](../backend/README.md) — `POST /v1/pipeline`, stages 1 and 2, server-configured Hugging Face key
- **UI:** [frontend/README.md](../frontend/README.md) — Vite app on port 5173, proxies `/api` → API on 3001

---

## Checklist

See `docs/TESTING.md`.
