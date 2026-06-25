# Prompts

Markdown system prompts and user-task preambles for pipeline stages. Filenames are referenced from `backend/config.toml` (`[prompts]`).

| File | Stage |
|------|-------|
| `01-resume-to-aptitude-profile.md` | Stage 1: aptitude profile (JSON) |
| `02-role-family-plan.md` | Stage 2: role family plan (JSON) |
| `03-job-discovery-synthesis.md` | Stage 3 synthesis: map ranked `found_jobs` → `verified_matches` JSON |

Stage 3 discovery is implemented in `backend/app/job_discovery/discovery.py` (role-family `search_terms` → `search_job_postings`; no prompt file).

Stage 3 fit ranking is implemented in `backend/app/job_discovery/aptitude_fit.py` (work-pattern scoring; no prompt file).

User-task preambles: `stage1-agent-user-task.txt`, `role-family-plan-user-task.txt`, `stage3-synthesis-user-task.txt`.

Contract: [docs/PROMPT-CONTRACT.md](../docs/PROMPT-CONTRACT.md).
