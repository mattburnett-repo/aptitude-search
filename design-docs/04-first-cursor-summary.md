> **Outdated snapshot (2026-05).** This file describes the repo before implementation. For the current product, see [README.md](../README.md) and [design-docs/README.md](README.md).

Exploring the workspace structure and key files.

## Workspace summary: aptitude-search

This repo is in an **early ideation / architecture phase**. There is **no application code** yet—only documentation and a Git repo.

### What it is

**Aptitude Search** is a planned **multi-stage LLM pipeline** for job search that focuses on **career targeting and search strategy**, not resume rewriting or application tracking.

Short description from the README:

> A multi-stage LLM pipeline for aptitude-driven job search, career targeting, and search strategy generation.

### Core idea (thesis)

Most job tools assume you already know what to search for and do **keyword/title matching**. This project aims to run **"career inference before search"**:

1. **Resume** → structured **aptitude profile** (skills, strengths, adjacent roles, seniority, etc.)
2. **Aptitude profile** → **job targeting strategy** (roles, keywords, company types, what to avoid)
3. **Strategy** → **search queries** (Boolean, LinkedIn, Indeed, variants)

The differentiator is **aptitude- and environment-driven targeting** (company type, fit, transferable strengths), not "optimize my resume for ATS."

### Files in the repo

| File | Purpose |
|------|---------|
| `README.md` | One-line project description |
| `01-first-concept-discussion.md` | Monetization paths (prompt pack, Notion, lightweight web app, user-configured API key, extension, SaaS) |
| `02-initial-concept-documentation.md` | Architecture, pipeline stages, prompt contract, vs Careerflow.ai, naming, status, next steps |
| `03-core-thesis.md` | USP: inference before search; person-model ↔ environment fit |

### Planned pipeline (from docs)

- **Stage 1 — Resume interpretation:** raw resume → aptitude profile
- **Stage 2 — Job targeting:** profile → roles, keywords, company types, seniority
- **Stage 3 — Query generation:** strategy → Boolean/LinkedIn/Indeed search strings

Future ideas: explainability, confidence signals, user correction loops, optional orchestration wrapper (location, salary, remote, etc.).

### Positioning vs existing tools

Docs contrast this with tools like **Careerflow.ai** (resume/ATS, tracking, application workflow). Aptitude Search is meant to sit **earlier in the funnel**: help decide **what** to target, not just execute applications faster.

### Status and intent

- **Private repo**, no license yet (IP/orchestration still forming)
- **No** `package.json`, source tree, prompts in repo, or infra—only planning docs
- Documented near-term steps: repo structure, schemas, modular prompts, orchestration prototype

### Bottom line

**aptitude-search** is a **concept and architecture notebook** for an aptitude-driven career-targeting LLM workflow, with monetization and productization ideas sketched but **not implemented**. If you want to go deeper next, we can walk through one doc (e.g. pipeline stages vs monetization) or outline what a minimal v1 repo layout would look like—still in Ask mode, guidance only unless you switch to Agent mode for implementation.
