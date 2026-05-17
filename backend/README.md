# Aptitude Search API (Python / FastAPI)

Orchestration for **Prompt 1** (aptitude profile JSON, schema-validated) and **Prompt 2** (verified job discovery as **plain text**—typically one `json` fenced block per the prompt; not schema-validated by the API).

**BYO OpenAI API key** via `X-OpenAI-Api-Key`. Optional `X-OpenAI-Model` (default `gpt-4o`).

Stage 2 does not perform live web search from the API—the user message asks the model to verify when possible, but only Cursor Agent (or similar) can browse. Use the API for stage 1 and drafts; use Agent for production-quality verification.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

## Validate fixtures

```bash
.venv/bin/python scripts/validate_fixtures.py
```

Validates stage-1 golden output only (`career-changer-mixed-stack-stage1.json`).

## Endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/health` | — | `{ "ok": true, "service": "aptitude-search-api" }` |
| POST | `/v1/pipeline` | `{ "resume", "constraints"? }` | `{ "aptitude_profile", "verified_matches" }` |
| POST | `/v1/stages/1` | `{ "resume" }` | `{ "aptitude_profile" }` |
| POST | `/v1/stages/2` | `{ "aptitude_profile", "constraints"? }` | `{ "verified_matches" }` |

All POST routes require header `X-OpenAI-Api-Key`. Optional `X-OpenAI-Model`.

`constraints` matches `schemas/constraints.schema.json` (location, remote_preference, salary_min, industries_include/exclude).

There is no `/v1/iterate` endpoint.

## Example

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Api-Key: $OPENAI_API_KEY" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

`verified_matches` is a string (raw LLM text). `aptitude_profile` is parsed JSON validated against `schemas/aptitude-profile.schema.json`.

## Implementation notes

- Prompts loaded from `prompts/01-resume-to-aptitude-profile.md` and `prompts/02-verified-job-discovery.md` (file body minus `#` title line).
- Stage 1 uses OpenAI `response_format: json_object`; stage 2 uses plain text completion.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` for the Vite dev server.
