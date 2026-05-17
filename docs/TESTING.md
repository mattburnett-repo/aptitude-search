# Manual testing checklist

## Stage 1 (Prompt 1)

- [ ] Output is valid JSON; parses against `schemas/aptitude-profile.schema.json`
- [ ] `core_skills` and `strengths` grounded in resume (spot-check 3 claims)
- [ ] At least one non-obvious `adjacent_roles` entry
- [ ] `rationale` present and readable

## Stage 2 (Prompt 2)

- [ ] SEARCH PLAN shows multiple angles from aptitude profile (not one ATS/board host)
- [ ] Rows use diverse employers and industries (≤2 per company, ≤3 per board domain)
- [ ] Columns: Company | Role title | Apply URL | Match description (no generic "AI broad search" column)
- [ ] Apply URL is a specific job or that employer's careers page—not a board search results page
- [ ] Description ties to aptitude profile evidence
- [ ] At most 20 rows; no padding

Prompt 2 quality depends on verifying postings with current information, not memory alone.

## Fixtures

```bash
cd backend && .venv/bin/python scripts/validate_fixtures.py
```

Validates `fixtures/example-outputs/career-changer-mixed-stack-stage1.json`.

## Models

Test on GPT-4o or 4.1 and Claude 3.5+ for stage 1 JSON. Stage 2 requires browsing for production quality.
