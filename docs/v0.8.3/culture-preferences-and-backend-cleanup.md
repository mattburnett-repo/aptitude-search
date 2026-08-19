# Culture preferences, interests, and backend cleanup (v0.8.3)

Ship resume-inferred **culture preferences** and **interests** as job-search inputs, plus backend wiring simplification already on `main` since v0.8.2.

## Why

Stage 1 extracted skills and work patterns but not workplace environment or subject draw. Those signals are not aptitude, but they belong in search: interest as hiring-shaped query terms, preference as Stage 2 avoid/families and Stage 3 fit. Thin example resumes could not support that extract, so Swagger’s default body is now a richer sample.

Separately, the backend flow review (Part A) simplified orchestration and tightened Stage 1 schema/prompt shape.

## User-facing behavior

- Aptitude profile always includes `culture_preferences` and `interests` (empty `[]` when the resume has no evidence).
- Profile UI shows those lists when non-empty; Stage 1 lead copy mentions them.
- Full pipeline: Stage 2 may use interests in `search_terms` and preferences in family choice / `avoid_terms`. Discovery fallback can query `interests`. Fit ranking scores `culture_preferences` against posting text.
- Swagger `POST /v1/pipeline` Try It Out uses Jordan Hale (`civic-climate-product-engineer.txt`) — employer types, volunteer, side projects, stated passions.
- Stage 2/3 result cards collapsed (PDF export still available).

## Backend

- Schema + Stage 1/2/3 prompts: `culture_preferences` and `interests` as labeled items.
- `normalize_aptitude_profile` treats both as labeled lists.
- `discovery.py` — `interests` as fallback query tokens (not preference adjectives).
- `aptitude_fit.py` — `culture_preferences` phrase-match scoring.
- `context.py` — both fields in synthesis compact profile.
- Earlier on this branch: Stage 2 moved into `pipeline.py`; `main.py` split (exception handlers, logging, observability); thinner Stage 1 normalizer; `profile_text` helpers.

## Frontend

- `AptitudeProfileDisplay` type + lists for the new fields.
- Stage 1 lead copy.
- Collapsed role-family and verified-matches cards (prior commits on this branch).
- Package version **0.8.3**.

## Tests

- Discovery: interests fill queries when roles/domains are empty; culture adjectives are not queried.
- Fit: culture preference labels boost matching snippets.
- Swagger example resume matches `civic-climate-product-engineer.txt`.
- Golden Stage 1 fixture includes the new keys.
- Frontend profile PDF page includes “Culture preferences”.

## Documentation

- `docs/v0.8.4/aptitude-premise.md` — premise (aptitude vs supporting signals); moved from `docs/APTITUDE-PREMISE.md`.
- `docs/v0.8.3/backend-flow-review.md` — Part A done / Part B notes (already on branch).
- `docs/video/` — demo pack (already on branch).
- Changelog: [`docs/changelog/0.8.3.md`](../changelog/0.8.3.md)

## Unchanged

- Constraints schema (remote/salary/location/industries) — not duplicated onto the profile.
- No personality field; no Stage 1 `fit` field.
- Embeddings still omit culture/interests.
- Input safety (Presidio / Prompt Guard), Tavily SERP-only discovery, O\*NET matching.

[0.8.3]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.8.3
