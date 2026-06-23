# Aptitude Search API (Python / FastAPI)

Orchestration for **Stage 1** (aptitude profile JSON, schema-validated) and **Stage 2** (profile-driven web search → synthesis LLM call → `verified_matches` JSON, schema-validated).

**Hugging Face keys** in `config.toml`:

- **Stage 1:** `[llm.aptitude].model_key` + `[llm.aptitude].model` — resume → aptitude profile (chat JSON).
- **Stage 2 discovery:** Python builds queries from profile + constraints and runs `search_job_postings` per skill (`[job_discovery].discovery_query_max`). No LLM for discovery.
- **Stage 2 synthesis:** `[llm.aptitude].model` + `[llm.job_discovery].temperature` — maps `found_jobs` to verified matches JSON.

See **[PROMPT-CONTRACT](../docs/PROMPT-CONTRACT.md)** for the full pipeline.

Smoke-test Stage 2 discovery: `.venv/bin/python scripts/smoke_job_discovery.py`

Stage 2 output is parsed and validated against `schemas/job-discovery-results.schema.json`.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # if config.toml is missing
# Edit config.toml: set [llm.aptitude].model_key
```

App settings live in `config.toml` (see `config.example.toml`). Loaded once via `app.core.config.config`.

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

**Try it:** Open [http://localhost:3001/docs](http://localhost:3001/docs) (Swagger UI) → `POST /v1/pipeline` → use the pre-filled **example** request body (from [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json)).

## Validate fixtures

```bash
.venv/bin/python scripts/validate_fixtures.py
```

Validates stage-1 golden output only (`career-changer-mixed-stack-stage1.json`).

## Tests

Requires a valid `config.toml` (same as [Setup](#setup)); pytest imports app config first and exits if that file is missing or invalid.

```bash
pip install -r requirements-dev.txt
pytest
```

During tests, `conftest.py` then swaps in `config.test.toml` so runs stay mocked and offline (no network or live API keys). Also run `scripts/validate_fixtures.py` for golden fixture schema checks.

## Endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/health` | — | `{ "ok": true, "service": "aptitude-search-api" }` |
| POST | `/v1/pipeline` | `{ "resume", "constraints"? }` | `{ "aptitude_profile", "verified_matches" }` |
| POST | `/v1/stages/1` | `{ "resume" }` | `{ "aptitude_profile" }` |
| POST | `/v1/stages/2` | `{ "aptitude_profile", "constraints"? }` | `{ "verified_matches" }` |

POST routes use the server-configured Hugging Face key and model from `[llm.aptitude]` in `config.toml` (Stage 2 discovery is Python-only; synthesis reuses the aptitude model).

`constraints` matches `schemas/constraints.schema.json` (location, remote_preference, salary_min, industries_include/exclude).

There is no `/v1/iterate` endpoint.

## Example

Full pipeline (resume + constraints):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @../fixtures/pipeline-request-example.json
```

Resume only:

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

`verified_matches` and `aptitude_profile` are parsed JSON validated against their schemas.

## Implementation notes

- Stage 1 system prompt: `prompts/01-resume-to-aptitude-profile.md` (file body minus `#` title line).
- **Stage 2a discovery:** `app/job_discovery/discovery.py` — profile-driven queries + `search_job_postings` (see [PROMPT-CONTRACT](../docs/PROMPT-CONTRACT.md)).
- Stage 2 synthesis: `prompts/03-job-discovery-synthesis.md` (chat JSON → `verified_matches`).
- Filenames are configured in `config.toml` under `[prompts]`.
- **URL filters (Stage 2):** blocked domains, path markers, and related SERP/`found_jobs` rules live in `app/job_discovery/url-filters.toml` (filename set by `[job_discovery].url_filters_file` in `config.toml`, resolved relative to `app/job_discovery/`). Add or remove entries in that file’s arrays (`skip_domains`, `skip_path_markers`, `skip_title_phrases`, `job_url_markers`); restart the API to pick up changes.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` for the Vite dev server.
