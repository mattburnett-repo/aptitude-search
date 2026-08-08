# LangGraph migration (backend spike)

Orchestrate the aptitude-search pipeline with LangGraph. Keep stage internals as plain Python. Do not turn this into an agent-framework rewrite.

Spike directory: `backend/lg_spike/` (named to avoid shadowing the installed `langgraph` package).

- Notebook: `backend/lg_spike/langgraph-migration.ipynb`
- Stage 3 module: `backend/lg_spike/stage3.py`
- Search substitute: `backend/lg_spike/search.py` (does **not** use `app.job_discovery.tools`)

## Working assumptions

1. **Leave existing `backend/app/` code as-is** — including `tools.py` and `pipeline.run_stage3`.
2. **All spike changes live under** `backend/lg_spike/` only.
3. Production FastAPI still uses the old sequential Stage 3 until an explicit swap.

## Spike Stage 3 search flow

```text
plan_queries
  → [Send] run_engine_search   # one worker per spike-local DDGS engine
  → reduce_filter_fit          # dedupe + URL filter + aptitude fit (defer=True)
  → synthesize
```

- **N** parallel workers from spike-local engines (not `job_discovery.search_backends`; production uses Tavily).
- Each worker runs discovery queries against **one** DDGS engine via `search.search_queries_on_backend`.
- `max_concurrency` defaults to `N` so all engines can run together.
- Downstream filter / fit / synthesize still import helpers from `app.job_discovery` (read-only).

## Linear pipeline (notebook)

```text
START → prepare_resume → stage1 → stage2 → stage3 → END
```

`stage3` node calls `stage3.run_stage3` (spike), not `app.pipeline.run_stage3`.

## Do / don’t

**Do:** change only files under `backend/lg_spike/`.

**Do not:** edit `app/job_discovery/tools.py` or any other `app/` module for this effort.

Official docs: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) (`Send` for map-reduce).
