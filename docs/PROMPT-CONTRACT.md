# Prompt contract

Every stage prompt in `prompts/` follows this structure.

## Sections

| Section | Purpose |
|---------|---------|
| **ROLE** | Stage identity (profiler, strategist, query optimizer, refinement editor) |
| **OBJECTIVE** | The single transformation this stage performs |
| **INPUT FORMAT** | What to paste or attach (raw text or prior-stage JSON) |
| **OUTPUT FORMAT** | Strict JSON matching the stage schema in `schemas/` |
| **RULES** | Behavioral constraints (no preamble, evidence vs inference, etc.) |

## Cross-cutting requirements

### Explainability

- Include a `rationale` array: 2–5 short, user-facing bullets.
- Do **not** output chain-of-thought or hidden reasoning.

### Confidence signaling

- Use `confidence`: `high` | `medium` | `low` on inferred items.
- Prefer `evidence_from_resume` when the resume supports a claim.
- Distinguish explicit evidence from inference in rationale text.

### Downstream safety

- Output **only** valid JSON (no markdown fences in production use; fences OK in docs examples).
- Do not invent skills, roles, or industries absent from the aptitude profile (Stages 2–3).
- Stage 2 must include `company_types`, `environment_fit`, and `roles_to_avoid` — not titles alone.

## Schema references

| Stage | Output schema |
|-------|----------------|
| 1 | `schemas/aptitude-profile.schema.json` |
| 2 | `schemas/targeting-strategy.schema.json` |
| 3 | `schemas/search-queries.schema.json` |
| Constraints (optional input) | `schemas/constraints.schema.json` |

## Versioning

Prompt pack version: **v1.0.0** (see root `CHANGELOG.md`).
