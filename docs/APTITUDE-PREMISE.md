# What is an aptitude? (premise, not current schema)

Thread log. First-principles only — not how Stage 1 / the schema currently behave.

---

## 2026-08-13 — Premise

**Question:** What exactly is an “aptitude”? Revisit the project premise; do not treat current app fields as the definition.

**Answer (summarized):** Aptitude is **a capacity to do a kind of thing well** — often before/beyond specific tools and titles. If the word is just a bag of skills, titles, and preferences, it is branding. The product has a distinct premise only if aptitude is **the thing that transfers when the keywords change**.

### Not aptitude

| Concept | Answers | Example |
|--------|---------|---------|
| Skill | What can they do with a tool/method? | Python, Salesforce |
| Knowledge | What do they know? | Logistics, HIPAA |
| Experience | What have they done? | 8 years, two migrations |
| Strength | What performance pattern shows up? | Ownership under ambiguity |
| Preference | What do they want? | Remote, mission-driven |
| Personality | How do they tend to behave? | Conscientious |
| Interest | What draws them? | Climate, ops |
| Fit | Match to a specific env/role | This startup, this posting |

### Three coherent meanings (pick one)

1. **Psychometric capacity** — stable-ish abilities (verbal, numerical, spatial, etc.). Resume is a weak source; needs tests.
2. **Demonstrated work capacity** — kinds of *work* they repeatedly succeed at, independent of stack (e.g. “bring order to messy systems”). Inferred from history.
3. **Occupational potential** — plausible role families they could grow into. A *prediction from* aptitude, not aptitude itself.

Culture preferences are none of the three; they constrain *where* capacity is applied.

### Proposed product definition

> An aptitude is a transferable capacity for a kind of work, evidenced by repeated success patterns — not the tools used to do it, and not what the person says they want.

Then: name those capacities (and confidence). Skills, domains, titles, culture, remote, salary sit around it as evidence or filters.

Alternative: psychometric (1) — but then a resume-only pipeline is the wrong instrument.

**Decision (updated):** extract aptitudes **and** still capture the nearby signals below as supporting context — they are not aptitude, but they are in scope.

---

## Subsequent turns

**Standing:** append this thread here; summarize.

- Start a markdown log of the aptitude-premise discussion; summarize where possible.
- Move `aptitude-premise.md` to `docs/` (folder name `v0.83` was a typo); delete `docs/v0.83/`.
- Rename to `docs/APTITUDE-PREMISE.md`.
- Use this file for subsequent turns in this thread.
- **Nearby concepts still in scope.** The “not aptitude” list (skill, knowledge, experience, strength, preference, personality, interest, fit) should still be captured / inferred on a good-faith basis. Keep them labeled as supporting signals, not as aptitude. Resume-friendliness varies: skill / knowledge / experience / strength are usually extractable; preference / interest / fit only when evidenced; personality is weakest (omit over invent).

### Resume-only capture vs codebase cost

**Can a resume support these?** (good-faith, omit over invent)

| Signal | Resume-only? | Notes |
|--------|----------------|-------|
| Skill | Yes | Resumes are built for this. |
| Knowledge | Partial | Domain/industry often present; depth vs name-drop is the risk. |
| Experience | Yes (facts) | Titles, tenure, employers, seniority. Timeline object not required to be useful. |
| Strength | Yes (infer) | Repeated patterns; keep evidence + confidence. |
| Preference | Weak | Rarely stated. Employer-type / environment patterns only. Remote/salary usually need user constraints, not the résumé. |
| Personality | No | Do not invent Big Five from bullets. Behavioral *work* patterns ≠ personality. |
| Interest | Weak | Only if stated (side projects, volunteer, “passionate about”). Do not equate industry with interest. |
| Fit | No (as extract) | Fit is a comparison to a posting/environment, computed later. Resume can only yield *environment history* (close to preference). |

**Already roughly covered by Stage 1 fields:** skill (`core_skills` / `secondary_skills`), knowledge (`domains`), experience (`seniority_band` + evidence), strength (`strengths`), some work-pattern overlap (`working_style_signals`). **Gaps:** preference, interest, personality (intentionally sparse), and treating “fit” as a Stage 1 field.

**Code change size** (`additionalProperties: false` on the profile schema means new keys are a real contract change):

1. **Prompt-only (small)** — tighten vocab in `01-resume-to-aptitude-profile.md` so existing fields map cleanly (domains = knowledge, strengths = strengths, working_style ≠ personality; empty `[]` when weak). No schema/UI if we don’t add keys. Does **not** give separately labeled preference/interest.
2. **New supporting fields (medium, bounded)** — e.g. `culture_preferences`, `interests` as optional labeled arrays (allow `[]`). Touch: schema, Stage 1 prompt + user-task, `normalize_aptitude_profile` labeled-key list, fixture(s), `AptitudeProfileDisplay` type + UI. Pipeline `run_stage1` itself does not care about field names. Skip a personality field unless evidence is explicit.
3. **Downstream wiring (optional, larger)** — only if those fields should affect search/rank/embed: `aptitude_fit.py`, `embedding.py`, Stage 2 prompt, `context.py` synthesis compact, maybe constraints overlap with remote. Not required to *capture* them.

**Do not** add Stage 1 `fit`. Keep it as ranking against jobs (Stage 3).

**Practical recommendation:** (2) for preference + interest; prompt rules for the rest; leave personality out; leave fit downstream.

### Preference / interest (focus) — personality dropped

**Personality:** out. Not useful or reliable from a resume.

Keep **preference** and **interest** as two labeled lists, not one blob, and not overloaded onto `domains` / `working_style_signals`.

| | Preference | Interest |
|--|------------|----------|
| Question | What *environment* do they fit / appear to want? | What *subject* draws them? |
| Resume evidence | Employer types, org context, repeated setting (nonprofit, startup, agency, regulated enterprise) | Stated passion, volunteer, side projects, consistent domain *choice* when they had options |
| Example labels | lean / resource-constrained; mission-driven; high-ambiguity product org | climate; games; healthcare access; operations |
| Not | Remote/salary (`constraints`); how they work (`working_style_signals`) | Where they happened to be employed (`domains` = knowledge) |

**Prompt rules:** `high` only if stated; pattern → `medium`/`low`; `[]` if none. Do not copy a domain into interest (“worked in logistics” ≠ “interested in logistics”). Preference labels are environment-shaped, not “wants remote.”

**Do not duplicate user constraints:** location, remote, salary, industries include/exclude stay on `constraints`. Resume inference is extra signal, not a second constraints object.

**Incorporate in layers (smallest first):**

1. **Capture + display** — `culture_preferences` + `interests` (labeled items, `[]` ok): schema, Stage 1 prompt, normalizer keys, fixture, profile UI.
2. **Stage 2 (next)** — interests may justify a non-obvious family or `avoid_terms`; preferences may shape `work_modes` / avoid (e.g. quota sales, heavy process). Still not search keywords.
3. **Stage 3 fit (later)** — phrase-match posting text like `strengths`. Skip as Tavily query terms: “mission-driven jobs” is a bad query. Interest as a single domain token is optional, same as today’s `domains` fallback.

**Not in this pass:** personality field; Stage 1 `fit`; wiring into discovery queries.
