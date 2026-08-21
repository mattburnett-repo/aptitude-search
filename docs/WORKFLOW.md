# Workflow

**Product workflow:** [Stage 1](../prompts/01-resume-to-aptitude-profile.md) → [Stage 2](../prompts/02-role-family-plan.md) → Stage 3 ([discovery + fit](../docs/PROMPT-CONTRACT.md) + [synthesis](../prompts/03-job-discovery-synthesis.md))

---

## Stage 1 — Aptitude profile

Resume text → structured aptitude profile JSON. See [prompts/README.md](../prompts/README.md).

---

## Stage 2 — Job types to try

Aptitude profile → job types to try JSON with `search_terms`, `work_modes`, and `avoid_terms`.

---

## Stage 3 — Verified job discovery

See [prompts/README.md](../prompts/README.md). Input: Stage 1 JSON, Stage 2 JSON, plus optional constraints (`schemas/constraints.schema.json`).

Discovery (Python): profile-driven queries + Exa search + listing gate → aptitude fit ranking → synthesis LLM → `verified_matches`.

---

## API

**API:** `POST /v1/pipeline` runs Stage 1 → 2 → 3 with no manual step. Individual stages: `POST /v1/stages/1`, `POST /v1/stages/2`, `POST /v1/stages/3`. Use Swagger at `http://localhost:3001/docs`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).
