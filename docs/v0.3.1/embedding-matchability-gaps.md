# Embedding matchability: fields left out of the edge

Short answer: **yes, there are things you could add — on both sides.** Some were deliberately left out; one big gap is that the O*NET mashup doesn’t match what your own design doc recommends.

## Aptitude side (what gets embedded today)

Only three fields:

- `aptitude_summary`
- `strengths`
- `working_style_signals`

**Left out of the embed (but in the profile):**

| Field | Worth adding? |
|-------|----------------|
| **`adjacent_roles`** | Maybe — market titles (“Platform Engineer”) that O*NET titles miss |
| **`domains`** | Maybe — industry context (logistics, nonprofit); O*NET has no industry node |
| **`core_skills` / `secondary_skills`** | Probably not — tends to pull matches toward “Software Developer” on stack overlap |
| **`seniority_band`** | Better as a **filter** (`job_zones`), not in the vector |
| **`rationale` / `confidence_map`** | No — meta, not match signal |

[`docs/v0.3.0/aptitude-to-jobtype-matching-edge.md`](../v0.3.0/aptitude-to-jobtype-matching-edge.md) says **`adjacent_roles` and `domains` are weak/optional on the embed side** — useful after the match or for validation, not primary.

## O*NET side (the mashup)

Today it’s: title, description, **abilities**, **skills**, alternate job titles.

The design doc actually wanted **`work_activities`** as the primary pairing with strengths — “what you do” language, not requirement checklists.

**Not in the mashup today (but available in O*NET):**

| O*NET source | Why it might help |
|--------------|-------------------|
| **`work_activities`** (top IM) | Best semantic match for strengths / work style |
| **`work_context`** | Remote/office, pace, autonomy |
| **`work_styles`** | Collaboration, initiative — pairs with `working_style_signals` |
| **`tasks`** | Finer-grain “what the job looks like” |
| **`knowledge`** | Domain-ish (finance, engineering) — secondary |

**Probably keep out of embed:** raw `abilities`/`skills` ratings as primary signal (docs note they’re *job requirements*, not person aptitude — and the current SQL includes them anyway).

## Bottom line

The biggest “did we leave something out?” item is probably **`work_activities` on the O*NET mashup**, not more aptitude fields. Aptitude side is intentionally narrow.

On the aptitude side, **`adjacent_roles` + `domains`** are the most plausible adds if you want richer matching — but test first; skills-heavy text often hurts.

If you want to experiment, the career-changer fixture pass/fail in [`docs/v0.3.0/aptitude-to-jobtype-matching-edge.md`](../v0.3.0/aptitude-to-jobtype-matching-edge.md) is the right sanity check: top matches should reflect modernization/integration work, not generic “Software Developer” on Python/Django overlap.
