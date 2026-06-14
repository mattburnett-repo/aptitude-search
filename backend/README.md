# Aptitude Search API (Python / FastAPI)

Orchestration for **Stage 1** (aptitude profile JSON, schema-validated) and **Stage 2** (web-search agent → synthesis LLM call → `verified_matches` JSON, schema-validated).

**Hugging Face keys** in `config.toml` (separate per stage; values may be the same token):

- **Stage 1:** `[llm.aptitude].model_key` + `[llm.aptitude].model` — resume → aptitude profile (chat JSON).
- **Stage 2:** `[llm.job_discovery].model_key` + `[llm.job_discovery].model` — job discovery **agent** (`smolagents` with web search + page scraping). Config: `[llm.job_discovery].max_steps`.

Smoke-test Stage 2 agent: `.venv/bin/python scripts/smoke_job_discovery_agent.py`

Stage 2 output is parsed and validated against `schemas/job-discovery-results.schema.json`.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # if config.toml is missing
# Edit config.toml: set [llm.aptitude].model_key and [llm.job_discovery].model_key
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

```bash
pip install -r requirements-dev.txt
pytest
```

Uses `config.test.toml` (no API keys or network). Also run `scripts/validate_fixtures.py` for golden fixture schema checks.

## Endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/health` | — | `{ "ok": true, "service": "aptitude-search-api" }` |
| POST | `/v1/pipeline` | `{ "resume", "constraints"? }` | `{ "aptitude_profile", "verified_matches" }` |
| POST | `/v1/stages/1` | `{ "resume" }` | `{ "aptitude_profile" }` |
| POST | `/v1/stages/2` | `{ "aptitude_profile", "constraints"? }` | `{ "verified_matches" }` |

POST routes use the server-configured Hugging Face keys and models from `config.toml` (per stage).

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
- Stage 2 discovery: `prompts/02-job-discovery-agent.md` + `prompts/job-discovery-code-agent.yaml` (`smolagents` CodeAgent).
- Stage 2 synthesis: `prompts/03-job-discovery-synthesis.md` (chat JSON → `verified_matches`).
- Filenames are configured in `config.toml` under `[prompts]`.
- **URL filters (Stage 2):** blocked domains, path markers, and related SERP/`found_jobs` rules live in `app/job_discovery/url-filters.toml` (filename set by `[job_discovery].url_filters_file` in `config.toml`, resolved relative to `app/job_discovery/`). Add or remove entries in that file’s arrays (`skip_domains`, `skip_path_markers`, `skip_title_phrases`, `job_url_markers`); restart the API to pick up changes.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` for the Vite dev server.
