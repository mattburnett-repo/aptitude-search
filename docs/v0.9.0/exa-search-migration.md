# Exa search migration (v0.9.0)

Replace Stage 3 web discovery’s [Tavily](https://tavily.com) search with [Exa](https://exa.ai). Keep the `search_job_postings` → aptitude fit → synthesis contract. Harden listing quality after semantic SERP noise that Exa surfaces.

## Why

Tavily served as a reliable API-backed SERP after the ddgs migration (0.8.0–0.8.2). Exa’s `auto` search fits aptitude-driven discovery better: natural-language / semantic retrieval over the open web, with query-relevant highlights for ranking and synthesis—without page scrape/extract.

Closes the provider swap left open in [`docs/v0.8.0/tavily-search-migration.md`](../v0.8.0/tavily-search-migration.md) ([issue #8](https://github.com/mattburnett-repo/aptitude-search/issues/8)).

## Implementation (production)

### Search

- `Exa.search` via `listing_gate.run_exa_search` → `tools.search_job_postings`.
- Default `type=auto` (configurable: `neural`, `fast`, `instant`, `deep`, `deep-lite`, `deep-reasoning`).
- `contents={"highlights": True}` → optional `found_jobs` snippets (no scrape/extract).
- Gate-built kwargs: `exclude_domains` / optional `include_domains` from `url-filters.toml`; `start_published_date` + `start_crawl_date` from `search_max_age_days`; at most **one** `exclude_text` phrase (≤5 words) from closed-listing phrases (Exa API limit).

### Listing gate (rejection authority)

Criteria: `app/job_discovery/url-filters.toml`  
Behavior: `app/job_discovery/listing_gate.py` only

| Layer | What it does |
|-------|----------------|
| Exa kwargs | Domains, dates, one closed-phrase `exclude_text` |
| SERP accept | Junk URL/title paths; closed phrases in highlights |
| Live probe | Optional HTTP check (`url_liveness_check`); drop 404/410/5xx shells; parking / error / challenge markers; Exa `get_contents` when challenged |

Thin search wrapper: `tools.py` (rate limit + Exa client + `filter_serp_rows`).

### Config (`[job_discovery]` / `[llm.job_discovery]`)

See `backend/config.example.toml`: `exa_api_key`, `search_type`, `search_max_age_days`, `url_liveness_*`, `discovery_query_max`, `result_top_k`, `url_filters_file`, plus search rate/snippet limits under `[llm.job_discovery]`.

Removed: `tavily_api_key`, `search_depth`, `search_min_score`.

### Role skew (Exa-surfaced)

Semantic search can over-recall adjacent/high-noise titles (e.g. data-scientist skew with low O\*NET). Mitigations in this release:

- Stage 2 prompt: prefer high O\*NET similarity bands.
- Discovery: weight/defer families and terms using `occupation_matches`.
- Aptitude fit: require alignment to search terms / adjacent roles; downweight soft-only signals.

### Out of scope

- Notebooks still use local DDGS until separately ported.
- Input guard / Presidio unchanged.
- Synthesis remains an HF chat call (`[llm.job_discovery]`); model choice is operator config, not a provider migration.

## Verification

- Unit tests mock Exa / listing gate (no live key required).
- Live `POST /v1/pipeline` with fixture resume returns schema-valid `verified_matches` after Exa-backed discovery + gate.

Changelog: [`docs/changelog/0.9.0.md`](../changelog/0.9.0.md)

[0.9.0]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.9.0
