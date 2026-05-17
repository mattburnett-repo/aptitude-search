# Prompts — how to run

**Workflow:** **Prompt 1** → **Prompt 2**

| File | Stage |
|------|--------|
| `01-resume-to-aptitude-profile.md` | Aptitude profile (JSON) |
| `02-verified-job-discovery.md` | Verified openings (TSV in markdown fence) |

`XX-original-aptitude-prompt.md` is **reference only** (pre-migration spec).

---

## Prompt 1 — Aptitude profile

1. Open the system prompt in `01-resume-to-aptitude-profile.md` (text inside the code fence).
2. Provide the resume (paste into the user template or attach `fixtures/sample-resumes/career-changer-mixed-stack.txt`).
3. Send:

```
Follow the system prompt in 01-resume-to-aptitude-profile.md.
Analyze the attached resume and return only the aptitude profile JSON.
```

4. Save the JSON reply.

---

## Prompt 2 — Verified openings

1. Open the system prompt in `02-verified-job-discovery.md`.
2. Paste the Prompt 1 JSON into the user template.
3. Send the user template from that file (with discovery rules filled in).
4. Copy the SEARCH PLAN and the tab-delimited table from the fenced block.

---

## Your resume

Use `resume-text.txt` at the repo root (gitignored) or any file under `fixtures/sample-resumes/`.
