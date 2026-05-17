# Prompts — how to run

**Workflow:** **Prompt 1** → **Prompt 2**

| File | Stage |
|------|--------|
| `01-resume-to-aptitude-profile.md` | Aptitude profile (JSON only) |
| `02-verified-job-discovery.md` | Verified job discovery (single JSON fenced block) |

`XX-original-aptitude-prompt.md` is **reference only** (pre-migration spec).

---

## Prompt 1 — Aptitude profile

1. Open `01-resume-to-aptitude-profile.md` (the file body is the system prompt).
2. Provide the resume (paste into the user template or attach a file under `fixtures/sample-resumes/`).
3. Send:

```
Follow the system prompt in 01-resume-to-aptitude-profile.md.
Analyze the attached resume and return only the aptitude profile JSON.
```

4. Save the JSON reply.

---

## Prompt 2 — Verified openings

1. Open `02-verified-job-discovery.md`.
2. Paste the Prompt 1 JSON into `<aptitude_profile>` in the user message (see [docs/HOW-TO-TEST-RUN-THE-PROMPTS.txt](../docs/HOW-TO-TEST-RUN-THE-PROMPTS.txt)).
3. Optionally fill `<constraints>` with JSON matching `schemas/constraints.schema.json`.
4. Send with discovery rules (employers first, diversify industries, confirm each posting is open).
5. Parse the single `json` fenced block: `search_plan` (3–6 strings), `results` (up to 20 verified postings), `notes` (verification caveats).

Use **Cursor Agent with web search** for live verification. The API runs the same prompt but does not browse.

---

## Your resume

Use `resume-text.txt` at the repo root (gitignored) or any file under `fixtures/sample-resumes/`.
