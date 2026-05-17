# Aptitude Search API (Python / FastAPI)

Orchestration for **Prompt 1** (aptitude profile JSON) and **Prompt 2** (verified matches text). **BYO OpenAI API key** via `X-OpenAI-Api-Key`. Optional `X-OpenAI-Model` (default `gpt-4o`).

Stage 2 does not perform live web search from the API—use Cursor Agent for verified listings.

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

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/v1/pipeline` | `{ "resume", "constraints"? }` → aptitude_profile + verified_matches |
| POST | `/v1/stages/1` | `{ "resume" }` → aptitude_profile |
| POST | `/v1/stages/2` | `{ "aptitude_profile", "constraints"? }` → verified_matches |

## Example

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Api-Key: $OPENAI_API_KEY" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```
