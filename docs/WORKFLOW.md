# Aptitude Search — Workflow Guide

**Product workflow:** [Prompt 1](../prompts/01-resume-to-aptitude-profile.md) → [Prompt 2](../prompts/02-verified-job-discovery.md)

**Run pipeline:** [backend/README.md](../backend/README.md) (Swagger at `/docs`)

`XX-original-aptitude-prompt.md` is the reference spec used to build Prompts 1 and 2.

---

## Resume source

**Demo:** `fixtures/sample-resumes/career-changer-mixed-stack.txt` (also `marketing-operations-lead.txt`, `senior-backend-engineer.txt`)

**Your resume:** `resume-text.txt` at repo root (gitignored)

---

## Prompt 1 — Aptitude profile

See [prompts/README.md](../prompts/README.md). Output: JSON only, conforming to `schemas/aptitude-profile.schema.json`.

## Prompt 2 — Verified job discovery

See [prompts/README.md](../prompts/README.md). Input: Prompt 1 JSON plus optional constraints (`schemas/constraints.schema.json`).

Output: one `json`-language fenced code block with `search_plan`, `results`, and `notes` per `schemas/job-discovery-results.schema.json`. No separate markdown headings—the UI and export read these fields from JSON.

**API:** `POST /v1/pipeline` runs Prompt 1 then Prompt 2; Stage 2 is job search (model instructed to search the web). Use Swagger at `http://localhost:3001/docs`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).

---

## Optional: API + web UI

- **API:** [backend/README.md](../backend/README.md) — `POST /v1/pipeline`, stages 1 and 2, server-configured Hugging Face key
- **UI:** [frontend/README.md](../frontend/README.md) — Vite app on port 5173, proxies `/api` → API on 3001

---

## Checklist

See `docs/TESTING.md`.
