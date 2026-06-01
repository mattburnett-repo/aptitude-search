# aptitude-search

Aptitude-driven job search: resume → aptitude profile → **verified openings only**.

## Product workflow

**[Prompt 1](prompts/01-resume-to-aptitude-profile.md)** → **[Prompt 2](prompts/02-verified-job-discovery.md)**

Steps: **[prompts/README.md](prompts/README.md)**

Reference (do not run): [`prompts/XX-original-aptitude-prompt.md`](prompts/XX-original-aptitude-prompt.md)

## Quick start

1. Set up and run the API — [backend/README.md](backend/README.md) (`uvicorn` on port **3001**).
2. Open **Swagger UI:** [http://localhost:3001/docs](http://localhost:3001/docs).
3. Call **`POST /v1/pipeline`** — use the pre-filled example request body, or paste from [`fixtures/pipeline-request-example.json`](fixtures/pipeline-request-example.json).

Example body (resume + Toronto remote SaaS/FinTech constraints):

```json
{
  "resume": "Product-minded software engineer with 7 years of experience building web applications. Strong in TypeScript, React, Node.js, and PostgreSQL. Built customer-facing SaaS features, improved performance, and partnered with design and product teams. Comfortable owning projects end-to-end, mentoring teammates, and working in agile environments.",
  "constraints": {
    "location": "Toronto, ON",
    "remote_preference": "remote",
    "salary_min": 110000,
    "industries_include": ["SaaS", "FinTech"],
    "industries_exclude": ["Gambling"]
  }
}
```

Or from the repo root (with the API running):

```bash
curl -s -X POST http://localhost:3001/v1/pipeline \
  -H "Content-Type: application/json" \
  -d @fixtures/pipeline-request-example.json
```

Response: `aptitude_profile` (JSON) and `verified_matches` (job search results). See **[docs/PROMPT-CONTRACT.md](docs/PROMPT-CONTRACT.md)** for how the pipeline works.

## Repository layout

```
prompts/          # 01 aptitude profile, 02 verified discovery; XX = reference
schemas/          # aptitude-profile, job-discovery-results, constraints
fixtures/         # sample resumes, pipeline-request-example.json, stage-1 golden output
docs/             # WORKFLOW, TESTING, PROMPT-CONTRACT
design-docs/      # original concept (historical); see design-docs/README.md
backend/          # FastAPI — stages 1 and 2
frontend/         # MVP UI (Vite + React)
```

## API + UI (optional)

- **[backend/README.md](backend/README.md)** — `POST /v1/pipeline`, server-configured Hugging Face key
- **[frontend/README.md](frontend/README.md)** — local dev on port 5173

## Plan

[.cursor/plans/aptitude-search-build.plan.md](.cursor/plans/aptitude-search-build.plan.md)
