# Aptitude Search — Workflow Guide

**Product workflow:** [Stage 1](../prompts/01-resume-to-aptitude-profile.md) → [Stage 1.5](../prompts/02-role-family-plan.md) → Stage 2 ([discovery + fit](../docs/PROMPT-CONTRACT.md) + [synthesis](../prompts/03-job-discovery-synthesis.md))

**Run pipeline:** [backend/README.md](../backend/README.md) (Swagger at `/docs`)

---

## Resume source

**Demo:** `fixtures/sample-resumes/career-changer-mixed-stack.txt` (also `marketing-operations-lead.txt`, `senior-backend-engineer.txt`)

**Your resume:** `resume-text.txt` at repo root (gitignored)

---

## Prompt 1 — Aptitude profile

See [prompts/README.md](../prompts/README.md). Output: JSON only, conforming to `schemas/aptitude-profile.schema.json`.

## Stage 1.5 — Role family plan

See [prompts/README.md](../prompts/README.md). Input: Stage 1 JSON. Output: JSON conforming to `schemas/role-family-plan.schema.json`.

## Stage 2 — Verified job discovery

See [prompts/README.md](../prompts/README.md). Input: Stage 1 JSON, Stage 1.5 JSON, plus optional constraints (`schemas/constraints.schema.json`).

The API runs three phases:

1. **Discovery** — Python builds queries from the role family plan `search_terms`, runs `search_job_postings` — collects `found_jobs`.
2. **Aptitude fit** — Python ranks/filters `found_jobs` by work-pattern fit (`strengths`, `working_style_signals`, plan `work_modes` / `avoid_terms`).
3. **Synthesis** (`03-job-discovery-synthesis.md`) — maps ranked `found_jobs` into schema-strict JSON with `search_plan`, `results`, and `notes` per `schemas/job-discovery-results.schema.json`.

Configure **`[job_discovery].discovery_query_max`**, **`aptitude_fit_min_score`**, and **`aptitude_fit_min_results`** in `backend/config.toml`. Details: [PROMPT-CONTRACT](PROMPT-CONTRACT.md).

**API:** `POST /v1/pipeline` runs Stage 1 → 1.5 → 2 with no manual step. Individual stages: `POST /v1/stages/1`, `POST /v1/stages/1.5`, `POST /v1/stages/2`. Use Swagger at `http://localhost:3001/docs`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).

---

## Optional: API + web UI

- **API:** [backend/README.md](../backend/README.md) — `POST /v1/pipeline`, stages 1 and 2, server-configured Hugging Face key
- **UI:** [frontend/README.md](../frontend/README.md) — Vite app on port 5173, proxies `/api` → API on 3001

---

## Testing

See [TESTING.md](TESTING.md) — run the API or UI for end-to-end checks; optional spot-checks when tuning prompts or discovery.
