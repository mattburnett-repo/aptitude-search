# Design docs (historical)

These files capture the **original exploration** of Aptitude Search (multi-stage targeting, query generation, monetization ideas). They are **not** the operational source of truth for the shipped product.

## What is implemented today

See the repo root [README.md](../README.md) and [docs/WORKFLOW.md](../docs/WORKFLOW.md):

1. **Prompt 1** — resume → aptitude profile JSON
2. **Prompt 2** — aptitude profile → verified job discovery JSON (`search_plan`, `results`, `notes`)
3. **API + MVP UI** — FastAPI (`backend/`) and Vite (`frontend/`)

The core thesis in [03-core-thesis.md](03-core-thesis.md) (career inference before search) still applies; the pipeline shape changed from “targeting strategy + search queries” to “verified openings only.”

## Files in this folder

| File | Role |
|------|------|
| [01-first-concept-discussion.md](01-first-concept-discussion.md) | Monetization paths, early prompt ideas |
| [02-initial-concept-documentation.md](02-initial-concept-documentation.md) | Original 3-stage architecture and prompt contract |
| [03-core-thesis.md](03-core-thesis.md) | USP: inference before search |
| [04-first-cursor-summary.md](04-first-cursor-summary.md) | Workspace snapshot (pre-implementation; outdated) |

Do not use these docs alone to run or test the product—use `prompts/` and `docs/` instead.
