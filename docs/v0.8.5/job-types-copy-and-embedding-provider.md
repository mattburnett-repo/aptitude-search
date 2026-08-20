# Job types copy, embedding provider, and Prompt Guard client reuse (v0.8.5)

Rename Stage 2 user-facing language from “role family plan” / “recommended roles” to **job types to try**, pin Hugging Face embeddings to a configurable `feature-extraction` provider, and reuse one Prompt Guard `InferenceClient` across resume chunks.

## Why

- “Role family plan” was opaque in progress logs, docs, and the wizard.
- Auto-routed embedding providers (e.g. DeepInfra) rejected `feature-extraction` for `BAAI/bge-large-en-v1.5`, so O\*NET matching failed silently.
- Prompt Guard created a new HF client per chunk; reusing one client cuts “Checking resume safety…” latency.

## User-facing behavior

- Wizard Step 4 title/summary: **Job types to try** (and related leads).
- Pipeline progress: `Stage 2: Finding job types to try…`
- Resume safety screening is unchanged in outcome; typically faster on multi-chunk resumes.

## Backend

- `[embedding].provider` required in config (example/test default `hf-inference`); validated against HF `PROVIDER_T`.
- Embedding `InferenceClient` uses `config.embedding.provider`.
- Prompt Guard: `@lru_cache` shared `_input_guard_client()`.
- `malicious_score_threshold` comment clarifies block threshold and higher/lower effect.

## Frontend

- Stage 4 hero and `RoleFamilyPlanDisplay` copy → job types to try.
- Package version **0.8.5**.

## Tests

- RoleFamilyPlanDisplay snapshot updated for “Why these job types”.
- Embedding unit tests still pass with provider config.

## Documentation

- READMEs, PROMPT-CONTRACT, WORKFLOW, one-sheet, prompts README: human-facing “job types to try”.
- Changelog: [`docs/changelog/0.8.5.md`](../changelog/0.8.5.md)

## Unchanged

- Internal identifiers (`role_family_plan`, schemas, prompt filenames).
- Injection cascade order (regex → blocklist → Prompt Guard) and fail-closed behavior.
- Stage 3 discovery / fit / synthesis logic.

[0.8.5]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.8.5
