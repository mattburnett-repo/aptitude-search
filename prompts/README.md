# Prompts

**Run the pipeline via the API** (primary): see [backend/README.md](../backend/README.md). Start the server, open **Swagger UI** at `http://localhost:3001/docs`, and call `POST /v1/pipeline` using the built-in example or [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json).

| File | Stage |
|------|--------|
| `01-resume-to-aptitude-profile.md` | Stage 1: aptitude profile (JSON) |
| `02-job-discovery-agent.md` | Stage 2a: discovery agent (web search + page visits) |
| `job-discovery-code-agent.yaml` | Stage 2a: smolagents prompt templates |
| `03-job-discovery-synthesis.md` | Stage 2b: map `found_jobs` → `verified_matches` JSON |

Reference only (not loaded by the API):

- `02-verified-job-discovery.md` — monolithic single-shot predecessor
- `XX-original-aptitude-prompt.md` — pre-migration spec

Prompt bodies (and the YAML templates) are loaded by the API per `backend/config.toml`. Edit these files to change behavior; no separate copy-paste runbook is required.

## Sample resume

Use `resume-text.txt` at the repo root (gitignored) or any file under `fixtures/sample-resumes/`.
