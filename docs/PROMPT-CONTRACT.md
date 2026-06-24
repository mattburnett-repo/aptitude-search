# Prompt contract

## Product model (canonical)

- **`POST /v1/pipeline`** runs Stage 1 (resume → aptitude profile), Stage 1.5 (profile → role family plan), then Stage 2 (plan-driven discovery → aptitude fit ranking → synthesis), with no manual step between stages.
- **Stage 2 is job search.** The API runs role-family-driven web discovery, ranks scraped postings by work-pattern fit, then a synthesis LLM call, and returns currently open postings in **`verified_matches`**.
- **Primary path:** API + UI (or Swagger). Prompt text lives under `prompts/` (see Stages table); filenames are wired in `backend/config.toml`.
- **Testing:** Swagger UI at `/docs` on the running API (see [backend/README.md](../backend/README.md)).
- **Implementation (not user-facing):** Stage 2 is three phases: (1) **discovery** — Python builds search queries from the **role family plan** `search_terms` (fallback: `adjacent_roles`, `domains`, skills), plus constraints, then runs `search_job_postings`; (2) **aptitude fit** — rank/filter `found_jobs` using `strengths`, `working_style_signals`, plan `work_modes` / `avoid_terms`; (3) **synthesis** — chat completion maps ranked `found_jobs` into schema-strict JSON. Result URLs are filtered to those observed in tool output. The API jsonschema-validates `verified_matches` against `job-discovery-results.schema.json`.

---

Stage 1, Stage 1.5, and Stage 2 synthesis prompts are schema-strict: the markdown file body (minus the `#` title line) is the system prompt loaded by the API.

## Sections (by stage)

| Section | Stage 1 | Stage 1.5 | Stage 2a (discovery) | Stage 2a (fit) | Stage 2b (synthesis) |
|---------|---------|-----------|------------------------|----------------|----------------------|
| **ROLE** | Career signal extraction | Work-mode mapping | Labor-market discovery | Aptitude fit ranking | Labor-market verification |
| **OBJECTIVE** | Resume → AptitudeProfile JSON | Profile → RoleFamilyPlan JSON | Find postings via web search | Rank/filter by work patterns | Map `found_jobs` → verified postings |
| **INPUT** | Resume text | AptitudeProfile JSON | RoleFamilyPlan + constraints | Profile + plan + `found_jobs` | Profile + plan + ranked `found_jobs` |
| **OUTPUT** | JSON only (`aptitude-profile.schema.json`) | JSON only (`role-family-plan.schema.json`) | `found_jobs` (internal) | ranked `found_jobs` (internal) | JSON only (`job-discovery-results.schema.json`) |

Cross-cutting:

- **Shared vocabulary** for `core_skills`, `secondary_skills`, `strengths`, `adjacent_roles`, `confidence`
- **Evidence vs inference** — prefer omission over invention
- **No preamble** — stage 1, 1.5, and stage 2b: JSON only (synthesis parses a single JSON object from the model)

## Stages

| Stage | Prompt file(s) | Output schema |
|-------|----------------|---------------|
| 1 | `01-resume-to-aptitude-profile.md` | `schemas/aptitude-profile.schema.json` |
| 1.5 | `02-role-family-plan.md` | `schemas/role-family-plan.schema.json` |
| 2a (discovery) | `app/job_discovery/discovery.py` (no prompt file) | `found_jobs` (internal; not the API response) |
| 2a (fit) | `app/job_discovery/aptitude_fit.py` (no prompt file) | ranked `found_jobs` (internal) |
| 2b (synthesis) | `03-job-discovery-synthesis.md` | `schemas/job-discovery-results.schema.json` |
| Constraints (optional, stage 2) | — | `schemas/constraints.schema.json` |

Related settings in `backend/config.toml`:

- **`[job_discovery].discovery_query_max`** — max `search_job_postings` calls per pipeline run (default `6`).
- **`[job_discovery].aptitude_fit_min_score`** — minimum work-pattern fit score to keep a scraped job (default `1`).
- **`[job_discovery].aptitude_fit_min_results`** — minimum jobs passed to synthesis when none meet `aptitude_fit_min_score` (default `2`).
- **`[llm.job_discovery]`** — search/scrape limits and synthesis temperature (`[llm.aptitude].model` is used for synthesis and stage 1.5 chat calls).

## API validation

| Stage | Validated by API? |
|-------|-------------------|
| 1 (aptitude profile) | Yes — `jsonschema` after LLM call |
| 1.5 (role family plan) | Yes — `jsonschema` after LLM call |
| 2 (verified matches) | Yes — `jsonschema` after synthesis; URLs filtered to tool-observed links |
| Constraints | Yes — when passed to pipeline/stage 2 |

## Versioning

Prompt pack version: **v1.0.0**. Product workflow is three LLM stages (1 → 1.5 → 2) with Python discovery and fit ranking between synthesis inputs. Earlier four-stage pack designs are superseded.
