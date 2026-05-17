# aptitude-search

Aptitude-driven job search: resume → aptitude profile → **verified openings only**.

## Product workflow

**[Prompt 1](prompts/01-resume-to-aptitude-profile.md)** → **[Prompt 2](prompts/02-verified-job-discovery.md)**

Steps: **[prompts/README.md](prompts/README.md)**

Reference (do not run): [`prompts/XX-original-aptitude-prompt.md`](prompts/XX-original-aptitude-prompt.md)

## Quick start

See **[prompts/README.md](prompts/README.md)** — Prompt 1 (resume → JSON), then Prompt 2 (profile → verified job discovery JSON). For live verification, use Cursor Agent with web search; see **[docs/HOW-TO-TEST-RUN-THE-PROMPTS.txt](docs/HOW-TO-TEST-RUN-THE-PROMPTS.txt)**.

## Repository layout

```
prompts/          # 01 aptitude profile, 02 verified discovery; XX = reference
schemas/          # aptitude-profile, job-discovery-results, constraints
fixtures/         # sample resumes + stage-1 golden output
docs/             # WORKFLOW, TESTING, PROMPT-CONTRACT
design-docs/      # original concept (historical); see design-docs/README.md
backend/          # FastAPI — stages 1 and 2
frontend/         # MVP UI (Vite + React)
```

## API + UI (optional)

- **[backend/README.md](backend/README.md)** — `POST /v1/pipeline`, BYO OpenAI key
- **[frontend/README.md](frontend/README.md)** — local dev on port 5173

## Plan

[.cursor/plans/aptitude-search-build.plan.md](.cursor/plans/aptitude-search-build.plan.md)
