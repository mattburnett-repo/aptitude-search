# Aptitude-to-jobtype matching edge: Stage 1 aptitude ↔ O*NET occupations

Where the vector-matching boundary sits in a large O*NET schema, and which fields participate on each side. Complements [`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md) and [`aptitude-embedding-summary.md`](./aptitude-embedding-summary.md).

---

## The edge (one sentence)

**One Stage 1 aptitude document ↔ one O*NET occupation (`onetsoc_code`), compared by embedding similarity.**

Not every table row. Not every rating. **~1,016 occupation nodes** on the O*NET side; **one composed profile** on the aptitude side per pipeline run.

```
Stage 1 AptitudeProfile          aptitude-to-jobtype          O*NET occupation
                                 matching (vector)
────────────────────────         ────────────────          ──────────────────
strengths                    ──►  embed as prose    ◄──►  description
working_style_signals              (one vector)            + top work activities
aptitude_summary                                           + sample alt titles
                                                           (one vector each)
                                      │
                                      ▼
                              top-K onetsoc_code(s)
                                      │
                                      ▼
                         job_titles → search_terms
                         related_occupations → expand
                         work_activities → fit_reason / work_modes
```

Everything else in Postgres is **material to build those two texts**, or **downstream use after the match** — not separate embedding targets.

---

## Stage 1: what goes on the edge

From `schemas/aptitude-profile.schema.json` and career-changer fixtures, fields sit at different semantic levels:

| Field | On the embedding edge? | Why |
|-------|------------------------|-----|
| **`strengths`** | **Yes — primary** | Work-pattern language (“transitional environments”, “end-to-end ownership”) |
| **`working_style_signals`** | **Yes — primary** | How they like to work; pairs with work activities / context |
| **`aptitude_summary`** | **Yes — glue** | Short narrative tying signals together |
| **`adjacent_roles`** | **Weak on embed side** | Market titles; better as validation or title crosswalk after SOC match |
| **`domains`** | **Optional** | Industry context; O*NET has no clean industry node |
| **`core_skills` / `secondary_skills`** | **No as primary** | “Python/Django” → keyword matching in vector form |
| **`seniority_band`** | **Filter, not embed** | Maps to `job_zones`, not similarity |
| **`rationale`** | **No** | Meta for humans/LLM |

**Aptitude-side text** (runtime, one doc per candidate):

```text
Summary: Adaptable full-stack engineer who succeeds where systems are being replaced...
Strengths: Thrives in transitional technical environments; End-to-end ownership under ambiguity; ...
Work style: High tolerance for ambiguity; Pragmatic builder over specialist researcher
```

Embed once per pipeline run.

---

## O*NET: what goes on the other side of the edge

The natural **retrieval unit** is `occupation_data` — one row per SOC code.

```sql
work_activities wa
JOIN content_model_reference cmr ON cmr.element_id = wa.element_id
WHERE wa.onetsoc_code = '...' AND wa.scale_id = 'IM'
```

| O*NET source | On the embedding edge? | Role |
|--------------|------------------------|------|
| **`occupation_data.description`** | **Yes — primary** | What this kind of work is |
| **`work_activities` (top IM)** + **`content_model_reference`** | **Yes — primary** | What you do — aligns with strengths |
| **`job_titles` (sample)** | **Yes — supporting** | Search-facing language; helps title gap |
| **`related_occupations`** | **No on embed** | Expand top-K after match |
| **`abilities` / `skills` / `knowledge` ratings** | **No as primary** | Requirement checklists; wrong vocabulary vs aptitude |
| **`work_styles`** | **Later** | Could augment explainability or second-pass filter |
| **`tasks` / `work_context`** | **Later / optional** | Finer grain; heavy; not first edge |

**O*NET-side text** (precomputed, one doc per `onetsoc_code`):

```text
Title: Software Developers
Summary: [description from occupation_data]
Work activities: Programming, Analyzing Data, Thinking Creatively, ...
Alternate titles: Application Developer, Software Engineer, ...
```

**~1,016 vectors**, stored e.g. in `occupation_embeddings` (not implemented yet).

---

## What is not the edge

| Not the edge | Why |
|--------------|-----|
| 73k `work_activities` rows | Occupation × activity × scale — wrong granularity |
| 93k `abilities` rows | Job *requirements*, not person aptitude |
| 57k `job_titles` rows | Many titles → one occupation; fold into occupation doc |
| `content_model_reference` alone | Dictionary of elements, not a role |
| Linkage tables (38–45) | Explainability metadata, not retrieval |

The **edge is occupation-level**, built by **rolling up** joins into prose on each side.

---

## What the edge outputs (downstream)

Vector search returns **SOC codes + scores**. Relational data does the rest:

| After match | O*NET table | Pipeline use |
|-------------|-------------|--------------|
| Search strings | `job_titles` | `search_terms` → Stage 3 |
| Adjacent roles | `related_occupations` | Expand / diversify families |
| Explain fit | top `work_activities` names | `fit_reason`, `work_modes` |
| Filter bad modes | low-scoring activities or context | `avoid_terms` |
| Seniority check | `job_zones` | Optional filter |

Stage 2 LLM can **augment** this (curated role families, market titles) rather than being replaced on day one.

Maps to existing Stage 2 plan fields ([`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md)):

| role_family plan | O*NET equivalent |
|------------------|------------------|
| role_family | O*NET-SOC title + occupational family |
| work_modes | Work activities / generalized work activities |
| search_terms | Alternate titles + related occupations |
| avoid_terms | Low-scoring / crosswalked-out occupations |
| fit_reason | “Matched because work activities X, Y align with strengths…” |

---

## Occupation document layers (SQL sources)

Each query pattern is a **layer** of the occupation-side document, not a separate match target:

1. `COUNT occupation_data` → corpus size (~1016)
2. `occupation_data` row → title + description backbone
3. `work_activities` by `element_id` → ranked features
4. **Join to `content_model_reference`** → semantic heart (human-readable work patterns)
5. `job_titles` → alternate titles for discovery
6. `related_occupations` → graph expansion after top-K

Query 4 is the key join: **aptitude strengths ↔ occupation work activities**, mediated by embedding both sides as narrative.

---

## Implementation sketch

```text
LEFT NODE:  f(stage1.strengths, stage1.working_style_signals, stage1.aptitude_summary)
RIGHT NODE: g(occupation_data, top_work_activities, sample_job_titles)  per onetsoc_code
EDGE:       cosine_similarity(embed(left), embed(right))
OUTPUT:     List[(onetsoc_code, score)]
```

- **`g(...)`** — precomputed offline, stored (e.g. pgvector or JSONL + numpy).
- **`f(...)`** — built at runtime from Stage 1 JSON.
- **`related_occupations` / full `job_titles`** — read from SQL after top-K, not embedded as separate nodes.

O*NET alone won't cover market titles (“Platform Engineer”, “RevOps”) — curated `role_family` rows sit **alongside** occupation vectors in the same index ([`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md)).

---

## Pass/fail test (career-changer fixture)

Embed the career-changer aptitude doc (`fixtures/example-outputs/career-changer-mixed-stack-stage1.json`) vs the occupation corpus.

**Success:** top occupations reflect *modernization, integration, analysis, stakeholder work* — and align with `career-changer-role-family-plan.json` (Solutions Engineer, Platform Engineer, etc.), not only generic “Software Developer” on skill overlap.

**Failure:** everything clusters on “Software Developers” because embedding input over-weighted `core_skills` or raw skill tables.

---

## Related docs

- [`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md) — integration plan, what to embed
- [`aptitude-embedding-summary.md`](./aptitude-embedding-summary.md) — semantic matching direction
- [`../v0.2.0/aptitude_refinement/next-steps.md`](../v0.2.0/aptitude_refinement/next-steps.md) — definitions of done
- [`../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md`](../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md) — aptitude-to-jobtype matching / job discovery / posting fit ranking framing

Tools: `data/load-onet-postgres.sh`, `data/smoke_onet_postgres.py`, `data/ingest/build_occupation_embeddings.py`
