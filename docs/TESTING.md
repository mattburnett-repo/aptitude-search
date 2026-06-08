# Manual testing checklist

## Stage 1 (Prompt 1)

- [ ] Output is valid JSON; parses against `schemas/aptitude-profile.schema.json`
- [ ] `core_skills` and `strengths` grounded in resume (spot-check 3 claims)
- [ ] At least one non-obvious `adjacent_roles` entry
- [ ] `rationale` present and readable

## Stage 2 (discovery agent + synthesis)

- [ ] `verified_matches` parses against `schemas/job-discovery-results.schema.json`
- [ ] `search_plan` has 3–6 strings drawn from the aptitude profile (not one ATS/board host)
- [ ] `results` use diverse employers and industries (≤2 per company, ≤3 per board domain)
- [ ] Each result has a direct apply/posting URL and `match_description` tied to profile evidence
- [ ] At most 20 results; no padding
- [ ] `notes` has 1+ meaningful search caveats (exclusions, limits, sparse results)

Stage 2 should reflect current postings (web search via the discovery agent), not memory alone. The API runs Stage 2 as part of `POST /v1/pipeline` and returns parsed, schema-validated `verified_matches`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).

## Fixtures

```bash
cd backend && .venv/bin/python scripts/validate_fixtures.py
```

Validates `fixtures/example-outputs/career-changer-mixed-stack-stage1.json` against the aptitude profile schema only.

**Note:** The committed golden file may fail until `confidence_map` values are objects `{ "confidence", "reason" }` per the schema (not bare strings). Regenerate from Prompt 1 if validation fails.

## Models

Test stage 1 on capable models for reliable JSON. Stage 2 via API uses the configured Hugging Face models (`aptitude_model` for stage 1, `job_discovery_model` for the agent and synthesis); quality depends on model and provider. Smoke-test the discovery agent: `backend/scripts/smoke_job_discovery_agent.py`.

## API smoke test (optional)

```bash
# Stage 1 only
curl -s -X POST http://localhost:3001/v1/stages/1 \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

Requires `llm.aptitude_model_key` and `llm.job_discovery_model_key` in `backend/config.toml`.

Full pipeline: `POST /v1/pipeline` — copy body from [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json) or use the Swagger example on `/docs`. See [backend/README.md](../backend/README.md).
