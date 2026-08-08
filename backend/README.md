# Aptitude Search API (Python / FastAPI)

Orchestration for **Stage 1** (aptitude profile), **Stage 2** (O\*NET vector match + role family plan), and **Stage 3** (plan-driven search → aptitude fit ranking → synthesis → `verified_matches` JSON, schema-validated).

**Hugging Face keys** in `config.toml`:

- **Stage 1:** `[llm.aptitude].model_key` + `[llm.aptitude].model` — resume → aptitude profile (chat JSON).
- **Ingress safety:** `[llm.input_guard]` — Prompt Guard 2 22M text-classification before Stage 1; Presidio PII deletion (`[input_safety]`). See [`docs/v0.5.0/input-safety.md`](../docs/v0.5.0/input-safety.md).
- **Stage 2:** same model/key — aptitude profile → role family plan (chat JSON).
- **Stage 3 discovery:** Python builds queries from the role family plan `search_terms` (fallback: profile `adjacent_roles` / `domains` / skills) and runs `search_job_postings` (`[job_discovery].discovery_query_max`). No LLM for discovery.
- **Stage 3 fit:** Python ranks found jobs by work-pattern fit and keeps `result_top_k` (`aptitude_fit.py`). No LLM.
- **Stage 3 synthesis:** `[llm.job_discovery].model_key` + `[llm.job_discovery].model` + `[llm.job_discovery].temperature` — maps ranked `found_jobs` to verified matches JSON.
- **O\*NET matching (Stage 2):** `[onet_matching]` in `config.toml` (required) — embeds the Stage 1 profile (`[embedding]`), queries `occupation_embeddings` via `[onet]` + pgvector, and grounds the Stage 2 LLM. Requires offline load: [`data/README.md`](../data/README.md).

See **[PROMPT-CONTRACT](../docs/PROMPT-CONTRACT.md)** for the full pipeline.

Smoke-test Stage 3 discovery: `.venv/bin/python scripts/smoke_job_discovery.py`

Stage 3 output is parsed and validated against `schemas/job-discovery-results.schema.json`.

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

**Try it:** Open [http://localhost:3001/docs](http://localhost:3001/docs) (Swagger UI) → `POST /v1/pipeline` → use the pre-filled **example** request body (from [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json)). Other sample resumes and request bodies: [`fixtures/sample-resumes/README.md`](../fixtures/sample-resumes/README.md).

## Validate fixtures

```bash
.venv/bin/python scripts/validate_fixtures.py
```

Validates golden Stage 1, Stage 2, and input-guard fixtures under `fixtures/example-outputs/`.

## Tests

Requires a valid `config.toml` (same as [Setup](#setup)); pytest imports app config first and exits if that file is missing or invalid.

```bash
pip install -r requirements-dev.txt
pytest
```

During tests, `conftest.py` then swaps in `config.test.toml` so runs stay mocked and offline (no network or live API keys). Also run `scripts/validate_fixtures.py` for golden fixture schema checks.

**O\*NET Postgres smoke** (optional integration; skipped unless enabled):

```bash
ONET_SMOKE_TEST=1 pytest tests/test_onet_smoke.py -v
```

Requires `config.toml` with a loaded O\*NET database (`[onet]`). See [`data/README.md`](../data/README.md).

## Endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/health` | — | `{ "ok": true, "service": "aptitude-search-api" }` |
| POST | `/v1/pipeline` | `{ "resume", "constraints"? }` | `{ "aptitude_profile", "role_family_plan", "occupation_matches", "verified_matches" }` |
| POST | `/v1/stages/1` | `{ "resume" }` | `{ "aptitude_profile" }` |
| POST | `/v1/stages/2` | `{ "aptitude_profile" }` | `{ "role_family_plan", "occupation_matches" }` |
| POST | `/v1/stages/3` | `{ "aptitude_profile", "role_family_plan"?, "constraints"? }` | `{ "verified_matches" }` |

POST routes use Hugging Face keys/models from `[llm.aptitude]` (Stages 1–2) and `[llm.job_discovery]` (Stage 3 synthesis) in `config.toml` (Stage 3 discovery is Python-only).

`constraints` matches `schemas/constraints.schema.json` (location, remote_preference, salary_min, industries_include/exclude).

There is no `/v1/iterate` endpoint.

## Example

Full pipeline (resume + constraints):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @../fixtures/pipeline-request-example.json
```

Resume only (career-changer):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

Entry-level profile with Kirksville constraints:

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @../fixtures/pipeline-request-pre-college.json
```

`verified_matches` and `aptitude_profile` are parsed JSON validated against their schemas.

## Implementation notes

- Stage 1 system prompt: `prompts/01-resume-to-aptitude-profile.md` (file body minus `#` title line).
- **Stage 3 discovery:** `app/job_discovery/discovery.py` — profile-driven queries + `search_job_postings` (see [PROMPT-CONTRACT](../docs/PROMPT-CONTRACT.md)).
- Stage 3 synthesis: `prompts/03-job-discovery-synthesis.md` (chat JSON → `verified_matches`).
- Filenames are configured in `config.toml` under `[prompts]`.
- **URL filters (Stage 3):** junk denylist for SERP rows lives in `app/job_discovery/url-filters.toml` (filename set by `[job_discovery].url_filters_file` in `config.toml`, resolved relative to `app/job_discovery/`). Edit `skip_domains`, `skip_path_markers`, `skip_title_phrases`; restart the API to pick up changes.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` for the Vite dev server.
