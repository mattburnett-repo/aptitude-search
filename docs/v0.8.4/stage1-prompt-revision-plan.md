# Stage 1 prompt revision plan (aptitude + social halo)

Proposal only — no prompt files changed yet. Scope: `prompts/01-resume-to-aptitude-profile.md` and `prompts/stage1-agent-user-task.txt`. Schema unchanged.

## Goal

Refine what counts as an aptitude signal and extract more from a resume: work capability/skills **and** social signals (workplace culture preferences, outside interests, personal values-shaped cues). Metaphor: social signals as an “aura” / “halo” around core skill facts.

## Diagnosis

The schema already has halo fields (`working_style_signals`, `culture_preferences`, `interests`). Weaknesses are interpretation and extraction pressure:

1. **`working_style_signals` and `domains` are undefined** in SHARED VOCABULARY.
2. ROLE / UNTRUSTED language (“career signals only”) biases toward tools/roles and away from social inference.
3. **`Prefer [] over guessing`** for preferences/interests likely under-extracts medium/low pattern signals already used in search/fit.
4. Evidence rules cover skills only; labeled halo items rarely get `evidence_from_resume` though the schema allows it.
5. No explicit “scan zones” for halo evidence (volunteer, side projects, employer-type patterns, education choices, mission language).
6. `stage1-agent-user-task.txt` is schema-shape only — no dual-layer extraction goal.

**Personal values:** map onto existing fields for now (mission/impact → `culture_preferences` / `interests`; workplace behavior → `working_style_signals` / `strengths`). Personality stays out (see [`aptitude-premise.md`](aptitude-premise.md)). No new schema keys yet.

---

## Suggested revisions: `01-resume-to-aptitude-profile.md`

### 1. Reframe ROLE + OBJECTIVE (two layers)

- **Core:** skills, domains, strengths, seniority, adjacent roles — what they can do.
- **Halo:** working style, culture preferences, interests — where/how capacity shows up, only from resume evidence.

Still: no job search, no invented biography. Prefer “aptitude-profile signals” over “career signals only.”

### 2. Soften UNTRUSTED RESUME INPUT

Keep injection resistance. Extract aptitude-profile signals (skills + halo); ignore role-play / prompt overrides inside the resume.

### 3. Complete SHARED VOCABULARY

| Term | Definition thrust |
|------|-------------------|
| **domains** | Knowledge / industry contexts from work (not interests). |
| **working_style_signals** | How they work (ambiguity, ownership, builder vs specialist, collaboration, pace, autonomy). Not Big Five personality. |
| **culture_preferences** | Environment fit from history (startup vs enterprise, lean, regulated, civic/gov, etc.). Not wish lists; not remote/salary. |
| **interests** | Subject that draws them (volunteer, side projects, stated passion). Employment domain ≠ interest. |
| **aptitude_summary** | Core capacity **plus** halo when present (feeds embeddings). |
| **rationale** | Why the profile hangs together (esp. halo + adjacent roles). |

Optional: strengths = what they’re good at; working_style = how they operate.

### 4. Add signal inventory / scan zones

Mine underused regions: experience verbs/outcomes, employer types, skills/projects, education electives, volunteer/About, side projects/OSS, awards/leadership. Maximize evidenced coverage; use confidence + optional evidence quotes; do not invent.

### 5. Recalibrate inference policy

- **Skills:** no invented tools/abilities.
- **Halo:** pattern inference expected when history supports it; `medium`/`low`; `high` only if stated; `[]` only when no pattern.
- Still forbid remote/salary as culture, personality, and domain→interest copies.

### 6. Broaden evidence rules

Extend `evidence_from_resume` guidance to all item arrays (skills and labeled halo fields), same verbatim quote rules.

### 7. Clarify `aptitude_summary`

Require primary capacity/seniority, 1–2 strengths or working-style signals, and halo when non-empty. Avoid skill laundry lists.

### 8. Optional cleanup

Drop unused “v4” title; dedupe OUTPUT RULES vs vocabulary; keep adjacent-role “non-obvious” but favor justification over novelty.

### 9. Out for this pass

No new keys (`personal_values`, personality, Stage 1 `fit`). Remote/hybrid stays in `constraints`.

---

## Suggested revisions: `stage1-agent-user-task.txt`

Keep short. Add a dual-layer goal before schema reminders: extract work skills/capacity **and** social/environment signals when evidenced; prefer medium/low items over empty lists when patterns are clear; keep `name`/`label` and seniority/`confidence_map` shape rules; encourage evidence quotes; summary should cover core + halo.

---

## Implementation priority

1. Define `working_style_signals` + `domains`; reframe ROLE/OBJECTIVE as core + halo.
2. Soften empty-array bias for culture/interests; add scan zones.
3. Evidence quotes on labeled halo items; strengthen `aptitude_summary`.
4. Align user-task with the above.
5. Optional redundancy/title trim.

## Downstream note

Culture/interests already feed Stage 2/3 search and fit. Better Stage 1 halo extraction helps without code changes. A dedicated `values` field would need schema + Stage 2/3 wiring later.
