# Prompt contract

## Product model (canonical)

- **`POST /v1/pipeline`** runs Stage 1 (resume → aptitude profile), then Stage 2 (profile + constraints → job search), with no manual step between stages.
- **Stage 2 is job search.** The model is instructed to search the web and return currently open postings in **`verified_matches`**.
- **Primary path:** API + UI (or Swagger). Same prompt text as `prompts/02-verified-job-discovery.md`.
- **Testing:** Swagger UI at `/docs` on the running API (see [backend/README.md](../backend/README.md)).
- **Implementation (not user-facing):** Stage 2 uses an LLM chat call (Hugging Face), not a separate jobs/search API in Python. The API jsonschema-validates `verified_matches` against `job-discovery-results.schema.json`.

---

Every stage prompt in `prompts/` follows a consistent structure. Stage prompts are schema-strict (v4/v6): the file body (minus the markdown title line) is the system prompt loaded by the API.

## Sections (by stage)

| Section | Stage 1 | Stage 2 |
|---------|---------|---------|
| **ROLE** | Career signal extraction | Labor-market verification |
| **OBJECTIVE** | Resume → AptitudeProfile JSON | AptitudeProfile → verified postings |
| **INPUT** | Resume text | AptitudeProfile JSON + optional constraints |
| **OUTPUT** | JSON only (`aptitude-profile.schema.json`) | Single `json` fenced block (`job-discovery-results.schema.json`) |
| **RULES** | Shared vocabulary, processing steps, no invention | Profile is immutable; verification and diversification rules |

Cross-cutting (both stages):

- **Shared vocabulary** for `core_skills`, `secondary_skills`, `strengths`, `adjacent_roles`, `confidence`
- **Evidence vs inference** — prefer omission over invention
- **No preamble** — stage 1: JSON only; stage 2: one fenced JSON block only

## Stages

| Stage | Prompt file | Output schema |
|-------|-------------|---------------|
| 1 | `01-resume-to-aptitude-profile.md` | `schemas/aptitude-profile.schema.json` |
| 2 | `02-verified-job-discovery.md` | `schemas/job-discovery-results.schema.json` |
| Constraints (optional, stage 2) | — | `schemas/constraints.schema.json` |

Reference only (not in the live workflow): `XX-original-aptitude-prompt.md`.

## API validation

| Stage | Validated by API? |
|-------|-------------------|
| 1 (aptitude profile) | Yes — `jsonschema` after LLM call |
| 2 (verified matches) | Yes — `jsonschema` after LLM call |
| Constraints | Yes — when passed to pipeline/stage 2 |

## Versioning

Prompt pack version: **v1.0.0**. Product workflow is two stages (1 → 2); earlier four-stage pack designs are superseded.
