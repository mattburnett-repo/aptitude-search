# Prompts

**Run the pipeline via the API** (primary): see [backend/README.md](../backend/README.md). Start the server, open **Swagger UI** at `http://localhost:3001/docs`, and call `POST /v1/pipeline` using the built-in example or [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json).

| File | Stage |
|------|--------|
| `01-resume-to-aptitude-profile.md` | Stage 1: aptitude profile (JSON) |
| `03-job-discovery-synthesis.md` | Stage 2b: map `found_jobs` → `verified_matches` JSON |

Stage 2a discovery is implemented in `backend/app/job_discovery/discovery.py` (profile-driven `search_job_postings`; no prompt file).

Reference only (not loaded by the API):

- `02-verified-job-discovery.md` — monolithic single-shot predecessor
- `XX-original-aptitude-prompt.md` — pre-migration spec

Prompt bodies are loaded by the API per `backend/config.toml`. See [PROMPT-CONTRACT](../docs/PROMPT-CONTRACT.md).

## Sample resume

Use `resume-text.txt` at the repo root (gitignored) or any file under `fixtures/sample-resumes/`.
