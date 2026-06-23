# Prompt contract

## Product model (canonical)

- **`POST /v1/pipeline`** runs Stage 1 (resume → aptitude profile), then Stage 2 (profile + constraints → job search), with no manual step between stages.
- **Stage 2 is job search.** The API runs profile-driven web discovery, then a synthesis LLM call, and returns currently open postings in **`verified_matches`**.
- **Primary path:** API + UI (or Swagger). Prompt text lives under `prompts/` (see Stages table); filenames are wired in `backend/config.toml`.
- **Testing:** Swagger UI at `/docs` on the running API (see [backend/README.md](../backend/README.md)).
- **Implementation (not user-facing):** Stage 2 is two phases: (1) **discovery** — Python builds search queries from the aptitude profile and constraints, then runs `search_job_postings` (DuckDuckGo search, URL filters, page scrape) for each query; (2) a single chat completion maps `found_jobs` into schema-strict JSON. Result URLs are filtered to those observed in tool output. The API jsonschema-validates `verified_matches` against `job-discovery-results.schema.json`.

---

Stage 1 and Stage 2 synthesis prompts are schema-strict: the markdown file body (minus the `#` title line) is the system prompt loaded by the API.

## Sections (by stage)

| Section | Stage 1 | Stage 2a (discovery) | Stage 2b (synthesis) |
|---------|---------|------------------------|----------------------|
| **ROLE** | Career signal extraction | Labor-market discovery | Labor-market verification |
| **OBJECTIVE** | Resume → AptitudeProfile JSON | Find postings via web search (`search_job_postings`) | Map `found_jobs` → verified postings |
| **INPUT** | Resume text | AptitudeProfile JSON + optional constraints | AptitudeProfile + constraints + `found_jobs` |
| **OUTPUT** | JSON only (`aptitude-profile.schema.json`) | `found_jobs` list (internal) | JSON only (`job-discovery-results.schema.json`) |
| **RULES** | Shared vocabulary, processing steps, no invention | Profile-driven queries + search/scrape | Profile is immutable; verification and diversification rules |

Cross-cutting:

- **Shared vocabulary** for `core_skills`, `secondary_skills`, `strengths`, `adjacent_roles`, `confidence`
- **Evidence vs inference** — prefer omission over invention
- **No preamble** — stage 1 and stage 2b: JSON only (synthesis parses a single JSON object from the model)

## Stages

| Stage | Prompt file(s) | Output schema |
|-------|----------------|---------------|
| 1 | `01-resume-to-aptitude-profile.md` | `schemas/aptitude-profile.schema.json` |
| 2a (discovery) | `app/job_discovery/discovery.py` (no prompt file) | `found_jobs` (internal; not the API response) |
| 2b (synthesis) | `03-job-discovery-synthesis.md` | `schemas/job-discovery-results.schema.json` |
| Constraints (optional, stage 2) | — | `schemas/constraints.schema.json` |

Related settings in `backend/config.toml`:

- **`[job_discovery].discovery_query_max`** — max `search_job_postings` calls per pipeline run (default `6`).
- **`[llm.job_discovery]`** — search/scrape limits and synthesis temperature (`[llm.aptitude].model` is used for the synthesis chat call).

## API validation

| Stage | Validated by API? |
|-------|-------------------|
| 1 (aptitude profile) | Yes — `jsonschema` after LLM call |
| 2 (verified matches) | Yes — `jsonschema` after synthesis; URLs filtered to tool-observed links |
| Constraints | Yes — when passed to pipeline/stage 2 |

## Versioning

Prompt pack version: **v1.0.0**. Product workflow is two stages (1 → 2); Stage 2 discovery is Python-driven; synthesis follows. Earlier four-stage pack designs are superseded.
