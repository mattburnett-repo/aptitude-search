# Tavily search migration (v0.8.0)

Replace Stage 3 web discovery’s DuckDuckGo/`ddgs` search path (and related `VisitWebpageTool` scraping) with [Tavily](https://tavily.com). Keep the existing `search_job_postings` output contract so discovery → aptitude fit → synthesis stay unchanged.

## Why

Stage 3 discovery previously depended on **`ddgs`** (multi-engine SERP) plus **smolagents `VisitWebpageTool`** for page scrape. That stack was **fragile and sometimes unreliable**: engine timeouts and flaky backends (e.g. Mojeek historically), inconsistent result quality across providers, and scrape failures on JS-heavy or blocked posting pages. Those failures surface as empty `found_jobs`, skipped URLs, or hard errors during live pipeline runs.

Moving to Tavily gives a single, API-backed search surface aimed at LLM/agent pipelines: stable auth, clearer rate limits, and SERP content shaped for downstream ranking/synthesis—not ad-hoc HTML scraping.

## Broader payoff

The migration is also a **provider-shaped seam** in the discovery tool layer. Once search is behind a small adapter (query in → title/url/snippet rows out), swapping or adding providers is cheaper. **Exa** (and similar search APIs) become incremental adapters rather than another rewrite of URL filters and `search_job_postings` JSON.

In short: fix reliability now; leave the door open for Exa and peers without locking the pipeline to one vendor’s SDK forever.

## Implementation (production)

Current path (as of **0.8.1**):

- **Search only:** `TavilyClient.search` → junk URL filter → SERP rows as `found_jobs` (title + URL; no page scrape / extract).
- **Config:** `job_discovery.tavily_api_key` (see `config.example.toml`). Removed `job_discovery.search_backends` (ddgs).
- **Code:** `backend/app/job_discovery/tools.py` — `TavilySdkClient` behind `TavilySearchClient`; `search_job_postings` JSON contract unchanged (`jobs` / `skipped` / `message`).
- **Deps:** `tavily-python` for production discovery; `ddgs` retained only for `lg_spike/`.
- **Out of scope here:** `backend/lg_spike/` still uses local DDGS until separately ported.

v0.8.0 briefly described a two-step search-then-extract design; **0.8.1** dropped extract for higher recall and a simpler Stage 3 path. See `docs/changelog/0.8.1.md`.
