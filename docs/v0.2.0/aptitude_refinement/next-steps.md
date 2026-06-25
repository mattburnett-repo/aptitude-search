# Aptitude refinement — next steps

A short, actionable plan distilled from the aptitude-matching direction discussion. See also [conversation-aptitude-matching-direction.md](../conversation-aptitude-matching-direction.md) and [aptitude-embedding-summary.md](../aptitude-embedding-summary.md) for full context.

---

## One sentence

**Stop searching on skills; start searching on the roles the profile already says the person could do — then explain and filter results using work patterns, not tool lists.**

Today `adjacent_roles` drive discovery when no role family plan is present; the full pipeline runs **Stage 2** to produce a formal role family plan that drives `search_terms`, `work_modes`, and `avoid_terms`.

---

## Definitions of done

Use these four criteria to judge whether a change is real progress (not keyword polish):

1. **Non-obvious roles show up** — results include justified roles the person wouldn't have searched manually. `adjacent_roles` is the primary test.
2. **Explanations cite work patterns** — match text references strengths / working style, not just "you know React."
3. **Wrong-mode jobs get dropped** — generic same-keyword postings that don't fit the actual work are filtered out.
4. **Every match is explainable** — tied to specific profile evidence, not vibes.

If a change doesn't move at least one of these, it's probably not worth doing yet.

---

## First step (smallest meaningful change) — **done**

**Make `adjacent_roles` drive what gets searched.** Implemented in `backend/app/job_discovery/discovery.py`:

- Search queries use **`adjacent_roles` labels** first, then **`domains`**, then **`core_skills` / `secondary_skills`** only as fallback when the profile has no roles or domains.
- Seniority + location/remote from constraints apply to domain and skill fallback queries; adjacent-role queries use the role label directly.

---

## What comes after (in order)

1. **Rank/filter scraped jobs** — **done** (`backend/app/job_discovery/aptitude_fit.py`). Uses `strengths`, `working_style_signals`, and role-family `work_modes` / `avoid_terms`. Config: `aptitude_fit_min_score`, `aptitude_fit_min_results`.
2. **Role-family plan** — **done** (Stage 2: `prompts/02-role-family-plan.md`, `schemas/role-family-plan.schema.json`, `POST /v1/stages/2`). Discovery uses plan `search_terms` when present.
3. **Embeddings** — not started. Point aptitude vectors at role semantics (curated role families + occupation taxonomies), not raw job postings.

---

## Pass/fail test

Run the career-changer resume through the pipeline:

| | Before (today) | After (success) |
|---|----------------|-----------------|
| Query focus | "Senior X Engineer" + stack keywords | Titles aligned to `adjacent_roles` |
| Results | Generic full-stack / Python roles | At least one Solutions Engineer, Platform Engineer, or similar adjacent role |
| Explanation | Skill overlap | Cites modernization / integration evidence from profile |

If results are still all "Senior Full Stack Engineer" with Python/Django, the change didn't land.

---

## Current gap (reference)

| Profile field | Used in discovery? | Used in fit ranking? | Used in synthesis? |
|---------------|-------------------|---------------------|-------------------|
| `core_skills` | Fallback only | No | Yes |
| `adjacent_roles` | Fallback (no plan) | Yes | Yes |
| `domains` | Fallback (no plan) | No | Yes (context only) |
| `strengths` | No | **Yes** | Yes |
| `working_style_signals` | No | **Yes** | Yes |
| role family `search_terms` | **Yes (primary)** | Yes | Yes |
| role family `work_modes` / `avoid_terms` | No | **Yes** | Yes |
| `seniority_band` | Yes (domain/skill fallback) | No | Yes |
| constraints (location, remote) | Yes | No | Yes |
| constraints (industries, salary) | **No** | No | Partial (narration only) |

The bottleneck is downstream usage of Stage 1 output, not richness of Stage 1 output.
