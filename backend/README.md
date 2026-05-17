# Aptitude Search API (Python / FastAPI)

Orchestration API for the prompt pipeline. **BYO OpenAI API key** via `X-OpenAI-Api-Key` header. Optional `X-OpenAI-Model` (default `gpt-4o`).

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If `pip` fails with a bad interpreter after moving this folder, run:

```bash
python3 -m venv .venv --clear
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Use the venv interpreter (avoids `ModuleNotFoundError` when global `uvicorn` is on your PATH):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 3001
```

## Validate golden fixtures

```bash
.venv/bin/python scripts/validate_fixtures.py
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/v1/pipeline` | Full run: `{ "resume", "constraints"? }` |
| POST | `/v1/stages/1` | `{ "resume" }` |
| POST | `/v1/stages/2` | `{ "aptitude_profile", "constraints"? }` |
| POST | `/v1/stages/3` | `{ "targeting_strategy" }` |
| POST | `/v1/iterate` | `{ "regenerate_from_stage", "current_artifacts", "user_corrections", "constraints"? }` |

## Example

```bash
curl -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Api-Key: $OPENAI_API_KEY" \
  -d '{"resume":"..."}'
```
