# Testing

## Normal path (end-to-end)

Run the stack and call the pipeline — Stages 1, 2, and 3 run automatically with schema validation on every response.

- **UI:** [frontend/README.md](../frontend/README.md) — `npm run dev` on port 5173
- **API:** [backend/README.md](../backend/README.md) — Swagger at `http://localhost:3001/docs` → `POST /v1/pipeline`

Example bodies:

- [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json) — civic/climate product engineer (preference/interest-rich), Toronto remote; resume text: [`civic-climate-product-engineer.txt`](../fixtures/sample-resumes/civic-climate-product-engineer.txt)
- [`fixtures/pipeline-request-pre-college.json`](../fixtures/pipeline-request-pre-college.json) — entry-level retail/service, Kirksville MO
- [`fixtures/pipeline-request-injection-test.json`](../fixtures/pipeline-request-injection-test.json) — should return **400** (input safety)

Sample resume text files: [`fixtures/sample-resumes/README.md`](../fixtures/sample-resumes/README.md).

Requires `[llm.aptitude].model_key` in `backend/config.toml`. See [PROMPT-CONTRACT.md](PROMPT-CONTRACT.md).

---

## Automated checks (offline, no live LLM)

**Backend unit/integration tests** (mocked; no network):

```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

`conftest.py` swaps in `config.test.toml` during tests.

**Frontend unit tests** (Vitest + Testing Library; no network):

```bash
cd frontend && npm ci && npm test
```

Typecheck and production build (also run in CI):

```bash
cd frontend && npm run build
```

GitHub Actions: **Backend tests** (`backend-tests.yml`) and **Frontend tests** (`frontend-tests.yml`) on path-filtered push/PR.

**Golden fixtures** (Stage 1 + Stage 2; registered in `backend/config.toml`):

```bash
cd backend && .venv/bin/python scripts/validate_fixtures.py
```

Validates `fixtures/example-outputs/career-changer-mixed-stack-stage1.json` against `aptitude-profile.schema.json` and `career-changer-role-family-plan.json` against `role-family-plan.schema.json`. There is no committed golden Stage 3 output — Stage 3 quality is judged when running the live pipeline (above).

**Stage 3 discovery smoke** (live web search; optional):

```bash
cd backend && .venv/bin/python scripts/smoke_job_discovery.py
```

---

## Optional quality spot-checks

Use when changing Prompt 1, discovery queries, URL filters, or synthesis — not required on every run if results are already acceptable.

### Stage 1

- [ ] `core_skills` and `strengths` grounded in resume (spot-check 3 claims)
- [ ] At least one non-obvious `adjacent_roles` entry
- [ ] `rationale` present and readable

### Stage 3

- [ ] `search_plan` reflects profile and constraints (not a single ATS/board host)
- [ ] `results` use diverse employers (≤2 per company, ≤3 per board domain)
- [ ] Each result has a direct posting URL and `match_description` tied to profile evidence
- [ ] At most 20 results; no padding
- [ ] `notes` has meaningful caveats (exclusions, limits, sparse results)

Stage 3 should reflect current postings from web search (`search_job_postings`), not model memory alone.

---

## Models and config

- **Stage 1 + Stage 3 synthesis:** `[llm.aptitude].model` and `[llm.aptitude].model_key`
- **Discovery tools + synthesis temperature:** `[llm.job_discovery]` (search/scrape limits, `temperature`)
- **Query budget:** `[job_discovery].discovery_query_max`

Use capable models for reliable Stage 1 JSON.

---

## curl examples

Stage 1 only:

```bash
curl -s -X POST http://localhost:3001/v1/stages/1 \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile r ../fixtures/sample-resumes/career-changer-mixed-stack.txt '{resume: $r}')"
```

Full pipeline (mid-career example):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @fixtures/pipeline-request-example.json
```

Full pipeline (entry-level, Kirksville constraints):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @fixtures/pipeline-request-pre-college.json
```

Resume file only (no constraints):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile r fixtures/sample-resumes/pre-college-retail-service.txt '{resume: $r}')"
```
