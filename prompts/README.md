# Prompts

**Run the pipeline via the API** (primary): see [backend/README.md](../backend/README.md). Start the server, open **Swagger UI** at `http://localhost:3001/docs`, and call `POST /v1/pipeline` using the built-in example or [`fixtures/pipeline-request-example.json`](../fixtures/pipeline-request-example.json).

| File | Stage |
|------|--------|
| `01-resume-to-aptitude-profile.md` | Aptitude profile (JSON) |
| `02-verified-job-discovery.md` | Verified job discovery (`verified_matches`) |

`XX-original-aptitude-prompt.md` is **reference only** (pre-migration spec).

Prompt bodies are loaded by the API as system prompts. Edit these files to change behavior; no separate copy-paste runbook is required.

## Sample resume

Use `resume-text.txt` at the repo root (gitignored) or any file under `fixtures/sample-resumes/`.
