# aptitude-search

Aptitude-driven job search: resume → aptitude profile → **verified openings only**.

## Product workflow

**[Prompt 1](prompts/01-resume-to-aptitude-profile.md)** → **[Prompt 2](prompts/02-verified-job-discovery.md)**

Steps: **[prompts/README.md](prompts/README.md)**

Reference (do not run): [`prompts/XX-original-aptitude-prompt.md`](prompts/XX-original-aptitude-prompt.md)

## Quick start

See **[prompts/README.md](prompts/README.md)** — Prompt 1 (resume → JSON), then Prompt 2 (JSON → verified openings).

## Repository layout

```
prompts/          # 01 aptitude, 02 verified discovery; XX = reference
schemas/          # aptitude-profile, constraints
fixtures/         # sample resumes + stage-1 golden output
docs/             # WORKFLOW, TESTING, PROMPT-CONTRACT
backend/          # FastAPI — stages 1 and 2
frontend/         # MVP UI
```

## Plan

[.cursor/plans/aptitude-search-build.plan.md](.cursor/plans/aptitude-search-build.plan.md)
