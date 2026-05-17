# Manual testing checklist

## Stage 1 (Prompt 1)

- [ ] Output is valid JSON; parses against `schemas/aptitude-profile.schema.json`
- [ ] `core_skills` and `strengths` grounded in resume (spot-check 3 claims)
- [ ] At least one non-obvious `adjacent_roles` entry
- [ ] `rationale` present and readable

## Stage 2 (Prompt 2)

- [ ] Response is a single `json`-language fenced code block (no preamble or extra markdown sections)
- [ ] JSON parses against `schemas/job-discovery-results.schema.json`
- [ ] `search_plan` has 3–6 strings drawn from the aptitude profile (not one ATS/board host)
- [ ] `results` use diverse employers and industries (≤2 per company, ≤3 per board domain)
- [ ] Each result has a direct apply/posting URL, `verification_status: "verified"`, and `match_description` tied to profile evidence
- [ ] At most 20 results; no padding
- [ ] `notes` has 1+ meaningful verification caveats (exclusions, limits, sparse results)

Prompt 2 quality depends on verifying postings with current information (web search / live pages), not model memory alone. The API returns stage 2 as plain text and does **not** schema-validate it—use Cursor Agent with browsing for production-quality verification.

## Fixtures

```bash
cd backend && .venv/bin/python scripts/validate_fixtures.py
```

Validates `fixtures/example-outputs/career-changer-mixed-stack-stage1.json` against the aptitude profile schema only.

**Note:** The committed golden file may fail until `confidence_map` values are objects `{ "confidence", "reason" }` per the schema (not bare strings). Regenerate from Prompt 1 if validation fails.

## Models

Test stage 1 on GPT-4o or 4.1 and Claude 3.5+ for reliable JSON. Stage 2 requires browsing for production-quality verification when run outside the API.

## API smoke test (optional)

```bash
# Stage 1 only
curl -s -X POST http://localhost:3001/v1/stages/1 \
  -H "Content-Type: application/json" \
  -H "X-OpenAI-Api-Key: $OPENAI_API_KEY" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

Full pipeline: `POST /v1/pipeline` with `{ "resume", "constraints"? }` — see [backend/README.md](../backend/README.md).
