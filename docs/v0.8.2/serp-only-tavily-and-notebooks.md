# SERP-only Tavily and notebooks relocation (v0.8.2)

Finish the Stage 3 path as **search → filter → rank → synthesize**, with no production page scrape. Relocate spike/exploration code under `backend/notebooks/`.

## Why

0.8.0 introduced Tavily; 0.8.1 dropped extract for higher recall. This release cleans up the remaining scrape-oriented production surface, wires useful Tavily knobs (depth, domain lists, score floor, snippets), and keeps experimental helpers out of the app import path.

## User-facing behavior

- `POST /v1/pipeline` Stage 3 still returns schema-valid `verified_matches` from web search + synthesis.
- Discovery quality can change with new defaults: domain exclude/include at search time, optional `search_min_score`, and SERP snippets on found jobs when content is present.
- No frontend changes.

## Backend

- **`tools.py`** — plain `search_job_postings(query)` calling Tavily with `search_depth`, `exclude_domains`, optional `include_domains`, and score filtering; maps hits to jobs via `normalize_result_url` and optional truncated `snippet`.
- **Config** — `job_discovery.search_depth`, `job_discovery.search_min_score`; scrape-only LLM discovery fields removed.
- **Removed from app** — `page_extract.py`, `tool_observed_urls.py` (moved to notebooks).
- **URL filters / utils** — SERP-oriented naming and helpers; junk denylist still applied post-search.

## Notebooks

- Renamed `backend/lg_spike/` → `backend/notebooks/`.
- Spike modules (`page_extract`, `tool_observed_urls`, heuristics, spike config) and `tavily-certification.ipynb` live under notebooks only.

## Tests

- Search posting tests mock `TavilyClient` and assert domain/score/snippet behavior.
- URL utils, filters, discovery, and aptitude-fit tests updated for the SERP-only path.

## Unchanged

- Stages 1–2 prompts and schemas.
- Synthesis still uses `[llm.aptitude].model` with `[llm.job_discovery]` temperature / max_tokens.
- Frontend package version (no web app changes in this release).

## See also

- Changelog: [`docs/changelog/0.8.2.md`](../changelog/0.8.2.md)
- Prior migration notes: [`docs/v0.8.0/tavily-search-migration.md`](../v0.8.0/tavily-search-migration.md)

[0.8.2]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.8.2
