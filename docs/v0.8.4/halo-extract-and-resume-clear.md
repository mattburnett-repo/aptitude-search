# Halo extract, resume clear, and Stage 1 planning (v0.8.4)

Extract culture preferences and interests when the resume shows them, leave those lists empty when it does not, and give the start page one clear control for PDF or pasted resume. Also: require TOML for backend path settings, and add Vitest markup snapshots.

## Why

Stage 1 already had `culture_preferences` and `interests` (v0.8.3), but the prompt preferred empty lists over extracting evidenced halo. That hid usable search inputs. The start page only offered “Clear file” for PDFs, not for pasted text or loaded `.txt` files.

## User-facing behavior

- Profiles fill **culture preferences** and **interests** when the resume evidences them; empty `[]` when it does not (no extra ritual).
- Stage 2 still turns hiring-shaped interests into `search_terms`; culture preferences stay out of Tavily query text (avoid/fit only).
- Confidence section heading: **Step 2 — How sure we are and why**.
- Start page: the same **Clear resume** control (circular X) next to a selected file name, and on the paste textarea when it has text.

## Backend

- Stage 1 prompts: extract halo when evidenced; `[]` if none; do not invent; do not copy a job domain into interests.
- `config.py`: prompt, schema, fixture, and `input_safety` settings must come from TOML (no Python fallbacks).
- `paths.py`: documented as the single repo-root `Path` resolver.

## Frontend

- `InferenceConfidenceDisplay` heading copy.
- `ResumeInput` uses `ClearFieldButton` / `FieldWithClear` for file and paste.
- Package version **0.8.4**.
- Vitest markup snapshots for display components (this branch).

## Tests

- ResumeInput: clear PDF and clear pasted text.
- Frontend display-component snapshots.

## Documentation

- `docs/v0.8.4/aptitude-premise.md` — aptitude vs supporting signals (moved from `docs/APTITUDE-PREMISE.md`).
- `docs/v0.8.4/stage1-prompt-revision-plan.md` — earlier, broader prompt-edit notes (not all implemented).
- `docs/v0.8.4/culture-interests-thin-resume-inference.md` — thin-resume inference notes (not encoded in full; ship is extract-if-present).
- Changelog: [`docs/changelog/0.8.4.md`](../changelog/0.8.4.md)

## Unchanged

- Aptitude profile schema (no new keys).
- Stage 2/3 search wiring for culture vs interests.
- Input safety ingress (regex / blocklist / Prompt Guard); prompt “untrusted resume” is still hardening only.
- Constraints (remote / salary / location / industries).

[0.8.4]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.8.4
