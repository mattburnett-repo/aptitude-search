# Embedding matchability: fields left out of the edge

Short answer: **yes, there are things you could add — on both sides.** Some were deliberately left out; one big gap is that the O*NET mashup doesn’t match what your own design doc recommends.

## Aptitude side (what gets embedded today)

Only four fields:

- `aptitude_summary`
- `strengths`
- `working_style_signals`
- `adjacent_roles`

**Left out of the embed (but in the profile):**

| Field | Worth adding? |
|-------|----------------|
| **`domains`** | Maybe — industry context (logistics, nonprofit); O*NET has no industry node |
| **`core_skills` / `secondary_skills`** | Probably not — tends to pull matches toward “Software Developer” on stack overlap |
| **`seniority_band`** | Better as a **filter** (`job_zones`), not in the vector |
| **`rationale` / `confidence_map`** | No — meta, not match signal |

[`docs/v0.3.0/aptitude-to-jobtype-matching-edge.md`](../v0.3.0/aptitude-to-jobtype-matching-edge.md) says **`adjacent_roles` and `domains` are weak/optional on the embed side** — useful after the match or for validation, not primary.

## O*NET side (the mashup)

Today it’s: title, description, **work activities** (top 10 IM), **abilities**, **skills**, alternate job titles.

**Not in the mashup today (but available in O*NET):**

| O*NET source | Why it might help |
|--------------|-------------------|
| **`work_context`** | Remote/office, pace, autonomy |
| **`work_styles`** | Collaboration, initiative — pairs with `working_style_signals` |
| **`tasks`** | Finer-grain “what the job looks like” |
| **`knowledge`** | Domain-ish (finance, engineering) — secondary |

**Probably keep out of embed:** raw `abilities`/`skills` ratings as primary signal (docs note they’re *job requirements*, not person aptitude — and the current SQL includes them anyway).

## Bottom line

Further experiments: **`domains`** on the aptitude side; **`work_context` / `work_styles`** on the O*NET mashup — test against the career-changer fixture before expanding.
