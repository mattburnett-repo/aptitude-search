# Prompt contract

Every stage prompt in `prompts/` follows this structure.

## Sections

| Section | Purpose |
|---------|---------|
| **ROLE** | Stage identity |
| **OBJECTIVE** | The single transformation this stage performs |
| **INPUT FORMAT** | What to paste or attach |
| **OUTPUT FORMAT** | Strict JSON (stage 1); SEARCH PLAN + JSON + NOTES (stage 2) |
| **RULES** | Behavioral constraints |

## Stages

| Stage | Prompt file | Output |
|-------|-------------|--------|
| 1 | `01-resume-to-aptitude-profile.md` | `schemas/aptitude-profile.schema.json` |
| 2 | `02-verified-job-discovery.md` | SEARCH PLAN + `job-discovery-results` JSON + NOTES |
| Constraints (optional, stage 2) | — | `schemas/constraints.schema.json` |

## Versioning

Prompt pack version: **v1.0.0** (see root `CHANGELOG.md`).
