# Aptitude Search — Workflow Guide

**Product workflow:** [Prompt 1](../prompts/01-resume-to-aptitude-profile.md) → [Prompt 2](../prompts/02-verified-job-discovery.md)

**Copy-paste steps:** [prompts/README.md](../prompts/README.md)

`XX-original-aptitude-prompt.md` is the reference spec used to build Prompts 1 and 2.

---

## Resume source

**Demo:** `fixtures/sample-resumes/career-changer-mixed-stack.txt`

**Your resume:** `resume-text.txt` at repo root (gitignored)

---

## Prompt 1 — Aptitude profile

See [prompts/README.md](../prompts/README.md). Output: JSON (`schemas/aptitude-profile.schema.json`).

## Prompt 2 — Verified job discovery

See [prompts/README.md](../prompts/README.md). Input: Prompt 1 JSON. Output: SEARCH PLAN + tab-delimited rows in a markdown fence.

---

## Checklist

See `docs/TESTING.md`.
