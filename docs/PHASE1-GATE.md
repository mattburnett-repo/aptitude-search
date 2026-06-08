# Phase 1 gate verification

Date: 2026-05-17  
Pack version: v1.0.0  
**Workflow at gate:** two prompts (aptitude profile → verified job discovery), not the earlier four-stage targeting/query pack.

## Exit criteria (current product)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Core prompts produce schema-valid JSON on diverse resumes | Pass (stage 1) | `prompts/01-resume-to-aptitude-profile.md`, `schemas/aptitude-profile.schema.json`, three sample resumes under `fixtures/sample-resumes/` |
| Stage 2 output matches job-discovery schema when run with verification | Manual | `prompts/02-job-discovery-agent.md`, `prompts/03-job-discovery-synthesis.md`, `schemas/job-discovery-results.schema.json`; API `POST /v1/pipeline` or `POST /v1/stages/2` |
| Human review: matches useful vs raw keyword dump | Manual | Review `results[].match_description` and `search_plan` diversity |
| Buyer doc sufficient for a stranger | Pass | `docs/WORKFLOW.md`, `backend/README.md` (Swagger), `prompts/README.md` |

## Automated fixture check

```bash
cd backend && .venv/bin/python scripts/validate_fixtures.py
```

Validates only:

- `fixtures/example-outputs/career-changer-mixed-stack-stage1.json`

There are no committed golden stage-2 outputs in the repo.

## Superseded (do not use for gate)

The following were planned in an earlier four-stage pack but are **not** in the repository:

- Prompts 3–4 (search queries, iteration)
- `targeting-strategy.schema.json`, `search-queries.schema.json`
- `fixtures/example-outputs/*-stage2.json`, `*-stage3.json`

## Gate decision

**Phase 1 gate: PASSED** for the two-stage verified-discovery workflow — API + MVP implementation authorized and present under `backend/` and `frontend/`.
