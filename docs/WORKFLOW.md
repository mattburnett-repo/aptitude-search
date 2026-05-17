# Aptitude Search — Workflow Guide (v1.0.0)

**Positioning:** Translate your resume into targeting strategy and search queries *before* you keyword-search.

**Time:** ~10 minutes for a first full run.

---

## What you need

- ChatGPT (4o/4.1), Claude (3.5+), or similar with a system/instructions field
- Your resume as plain text
- The four prompt files in `prompts/`

---

## Steps

### 1. Aptitude profile (Prompt 1)

1. Open `prompts/01-resume-to-aptitude-profile.md`.
2. Copy the **System prompt** into your AI tool’s system/instructions area.
3. Paste the **User prompt template**, replace `{{RESUME_TEXT}}` with your resume.
4. Save the JSON response. Validate structure against `schemas/aptitude-profile.schema.json` (optional: use a JSON Schema validator).

### 2. Targeting strategy (Prompt 2)

1. Open `prompts/02-aptitude-to-targeting-strategy.md`.
2. Set the system prompt.
3. Paste Stage 1 JSON into `{{APTITUDE_PROFILE_JSON}}`.
4. Optional: set constraints, e.g.:

```json
{
  "location": "Portland, OR",
  "remote_preference": "remote",
  "salary_min": 120000,
  "industries_include": ["healthcare SaaS"],
  "industries_exclude": ["defense"]
}
```

5. Save the targeting strategy JSON.

### 3. Search queries (Prompt 3)

1. Open `prompts/03-targeting-to-search-queries.md`.
2. Paste Stage 2 JSON into `{{TARGETING_STRATEGY_JSON}}`.
3. Use the returned Boolean, LinkedIn, and Indeed strings in each platform.
4. Start with the **balanced** search variant unless you need maximum reach (broad) or laser focus (narrow).

### 4. Refine (Prompt 4, optional)

If something is wrong (seniority, industry, role focus):

1. Open `prompts/04-iteration-refinement.md`.
2. Set `regenerate_from_stage` to `2` (strategy + queries) or `3` (queries only).
3. Include current JSON in `current_artifacts` and describe fixes in `user_corrections`.

---

## Tips

- **Run stages in order.** Each stage assumes the previous JSON shape.
- **Review rationale arrays** — they explain *why*, not just *what*.
- **Company types matter more than job titles** for this workflow; read Stage 2 carefully before searching.
- Compare your output to `fixtures/example-outputs/` for shape and specificity.

---

## Web app (optional)

If you prefer a guided UI with BYO API key, run the MVP:

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --port 3001

cd frontend && npm install && npm run dev
```

See `backend/README.md` and `frontend/README.md`.

---

## Model notes

- **GPT-4o / 4.1:** Generally follows JSON-only rules well; remind “no markdown” if needed.
- **Claude 3.5+:** Strong reasoning on adjacent roles; may need “output raw JSON only” repeated in user message.
- If JSON is wrapped in fences, strip fences before saving or passing to the next stage.

---

## Support checklist

Before considering a run “done,” see `docs/TESTING.md`.
