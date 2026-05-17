# Manual testing checklist

Run after any prompt or schema change. Test on **all** fixtures in `fixtures/sample-resumes/`.

## Per-resume pipeline

- [ ] **Stage 1:** Output is valid JSON; parses against `schemas/aptitude-profile.schema.json`
- [ ] **Stage 1:** `core_skills` and `strengths` are grounded in resume text (spot-check 3 claims)
- [ ] **Stage 1:** `adjacent_roles` are non-obvious vs keyword extraction (at least one surprise fit)
- [ ] **Stage 2:** Output parses against `schemas/targeting-strategy.schema.json`
- [ ] **Stage 2:** No skill/role appears that contradicts Stage 1 profile
- [ ] **Stage 2:** `company_types` and `environment_fit` are present and specific (not generic fluff)
- [ ] **Stage 2:** `roles_to_avoid` has at least one entry with `why`
- [ ] **Stage 3:** Output parses against `schemas/search-queries.schema.json`
- [ ] **Stage 3:** Boolean/LinkedIn/Indeed queries use `keyword_clusters` from Stage 2
- [ ] **Stage 3:** `search_variants` includes broad, balanced, and narrow
- [ ] **All stages:** `rationale` arrays are present and readable

## Iteration (Prompt 4)

- [ ] Apply one user correction (e.g. wrong seniority or missed strength)
- [ ] Downstream JSON updates without full pipeline rerun when `regenerate_from_stage` is 2 or 3
- [ ] Corrected field reflected in regenerated output

## Models

Test on at least:

- [ ] OpenAI GPT-4o or 4.1
- [ ] Anthropic Claude 3.5 Sonnet or newer

Note model-specific quirks in `docs/WORKFLOW.md`.

## Phase 1 gate (before API work)

- [ ] All three core prompts pass this checklist on 3+ diverse resumes
- [ ] Human review: targeting feels useful vs raw keyword search
- [ ] `docs/WORKFLOW.md` is sufficient for a stranger to run the pack

## API (Phase 2 — Python/FastAPI)

- [ ] `cd backend && python scripts/validate_fixtures.py` passes
- [ ] `POST /v1/pipeline` returns same quality as manual run on fixtures
- [ ] All API responses validate against stage schemas
- [ ] MVP runs locally with BYO API key in browser only
