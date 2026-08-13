# Prompt contract

## Product model (canonical)

- **`POST /v1/pipeline`** runs Stage 1 (resume → aptitude profile), Stage 2 (profile → role family plan), then Stage 3 (plan-driven discovery → aptitude fit ranking → synthesis), with no manual step between stages.
- **Stage 3 is job search.** The API runs role-family-driven web discovery, ranks found postings by work-pattern fit, then a synthesis LLM call, and returns currently open postings in **`verified_matches`**.
- **Primary path:** API + UI (or Swagger). Prompt text lives under `prompts/` (see Stages table); filenames are wired in `backend/config.toml`.
- **Testing:** Swagger UI at `/docs` on the running API (see [backend/README.md](../backend/README.md)).
- **Implementation (not user-facing):** Stage 3 is three phases: (1) **discovery** — Python builds search queries from the **role family plan** `search_terms` (fallback: `adjacent_roles`, `domains`, `interests`, skills), plus constraints, then runs `search_job_postings`; (2) **aptitude fit** — rank/`top_k` filter on `found_jobs` (including `culture_preferences`); (3) **synthesis** — chat completion maps ranked `found_jobs` into schema-strict JSON with match explanations. The API jsonschema-validates `verified_matches` against `job-discovery-results.schema.json`.

---

Stage 1, Stage 2, and Stage 3 synthesis prompts are schema-strict: the markdown file body (minus the `#` title line) is the system prompt loaded by the API.

## Sections (by stage)

| Section | Stage 1 | Stage 2 | Stage 3 discovery | Stage 3 fit | Stage 3 synthesis |
|---------|---------|---------|-------------------|-------------|-------------------|
| **ROLE** | Career signal extraction | Work-mode mapping | Labor-market discovery | Aptitude fit ranking | Labor-market verification |
| **OBJECTIVE** | Resume → AptitudeProfile JSON | Profile → RoleFamilyPlan JSON | Find postings via web search | Rank/filter by work patterns | Map `found_jobs` → verified postings |
| **INPUT** | Resume text | AptitudeProfile JSON | RoleFamilyPlan + constraints | Profile + plan + `found_jobs` | Profile + plan + ranked `found_jobs` |
| **OUTPUT** | JSON only (`aptitude-profile.schema.json`) | JSON only (`role-family-plan.schema.json`) | `found_jobs` (internal) | ranked `found_jobs` (internal) | JSON only (`job-discovery-results.schema.json`) |

Cross-cutting:

- **Shared vocabulary** for `core_skills`, `secondary_skills`, `strengths`, `adjacent_roles`, `culture_preferences`, `interests`, `confidence`
- **Evidence vs inference** — prefer omission over invention
- **No preamble** — stages 1, 2, and 3 synthesis: JSON only (synthesis parses a single JSON object from the model)

## Stages

| Stage | Prompt file(s) | Output schema |
|-------|----------------|---------------|
| 1 | `01-resume-to-aptitude-profile.md` | `schemas/aptitude-profile.schema.json` |
| 2 | `02-role-family-plan.md` | `schemas/role-family-plan.schema.json` |
| 3 discovery | `app/job_discovery/discovery.py` (no prompt file) | `found_jobs` (internal; not the API response) |
| 3 fit | `app/job_discovery/aptitude_fit.py` (no prompt file) | ranked `found_jobs` (internal) |
| 3 synthesis | `03-job-discovery-synthesis.md` | `schemas/job-discovery-results.schema.json` |
| Constraints (optional, stage 3) | — | `schemas/constraints.schema.json` |

Related settings in `backend/config.toml`:

- **`[job_discovery].discovery_query_max`** — max `search_job_postings` calls per pipeline run (default `6`).
- **`[job_discovery].result_top_k`** — max ranked jobs passed to synthesis after aptitude fit (default `25`).
- **`[llm.job_discovery]`** — synthesis model/temperature and search limits (`search_max_results`, `search_rate_limit`). Spike-only scrape knobs have defaults.

## API validation

| Stage | Validated by API? |
|-------|-------------------|
| 1 (aptitude profile) | Yes — `jsonschema` after LLM call |
| 2 (role family plan) | Yes — `jsonschema` after LLM call |
| 3 (verified matches) | Yes — `jsonschema` after synthesis; URLs filtered to tool-observed links |
| Constraints | Yes — when passed to pipeline/stage 3 |

## Versioning

Prompt pack version: **v1.0.0**. Product workflow is three LLM stages (1 → 2 → 3) with Python discovery and fit ranking between synthesis inputs. Earlier four-stage pack designs are superseded.
