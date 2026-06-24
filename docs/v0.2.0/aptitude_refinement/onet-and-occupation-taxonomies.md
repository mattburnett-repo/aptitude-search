# O*NET and occupation taxonomies for Layer A matching

Yes — for Layer A (aptitude → role semantics), O*NET or a similar taxonomy is the right kind of “other side of the embedding,” not job postings. The project docs already point there; nothing in the codebase wires it up yet.

## Why O*NET fits this project

O*NET gives you a finite, stable, explainable corpus (~1,000 SOC occupations) with:

- occupation summaries and alternate titles
- work activities and tasks (good for work-pattern matching)
- skills / knowledge / abilities (use carefully — easy to fall back into keyword land)
- interest/work-style dimensions (optional later)

That maps cleanly onto what the pipeline already produces in Stage 1.5:

| Your role_family plan | O*NET equivalent |
|-----------------------|------------------|
| role_family | O*NET-SOC title + occupational family |
| work_modes | Work activities / generalized work activities |
| search_terms | Alternate titles + related occupations |
| avoid_terms | Low-scoring / crosswalked-out occupations |
| fit_reason | “Matched because work activities X, Y align with strengths…” |

O*NET is broad (not SWE-only) and normalized — good for career-changer / adjacent-role discovery. It lags market titles (“Staff Platform Engineer” won’t be a first-class row), which is why the refinement docs say: O*NET bootstrap + curated role families on top.

## API vs bulk download

Two real integration paths:

### 1. O*NET Web Services (live API)

- Sign up: https://services.onetcenter.org/ — free, X-API-Key, JSON REST, OpenAPI spec
- Good for: keyword search by title, occupation reports, crosswalks, prototyping
- Weak for: embedding index at pipeline latency — rate limits, “best effort” uptime; docs recommend local DB or cache for production volume

Use at runtime for: “given this job title, what SOC code is closest?” (crosswalk), not “embed all occupations every pipeline run.”

### 2. Downloadable O*NET Database (local)

- Periodic bulk release (API tracks current DB, e.g. 30.x)
- Good for: build a static embedding corpus once, version it in repo or data/, no runtime dependency
- This is what you want for Layer A matching in POST /v1/pipeline

Practical pattern: bulk download → ETL script → data/occupations/onet_corpus.jsonl → precomputed embeddings → cosine search offline or in-process.

## What to embed from O*NET (important)

Don’t embed skill checklists alone — that recreates keyword search in vector form.

Embed a narrative doc per occupation, for example:

Title: Software Developers
Summary: [O*NET description]
Work activities: [top N activities as prose]
Typical context: [technology design, systems analysis, ...]
Alternate titles: [...]

Weight work activities + description higher than raw “Skills” tables. That aligns with the aptitude side (strengths, working_style_signals) rather than core_skills.

## How it slots into the pipeline

Stage 1 (aptitude profile)
    ↓ embed work-pattern fields
Layer A: similarity vs [O*NET corpus + curated role_families]
    ↓ top-K occupations + your curated families
Stage 1.5 (augment or replace LLM plan)
    ↓ search_terms from matched titles + curated typical_titles
Stage 2 discovery (unchanged — keyword/search API)
    ↓
Layer C: re-rank scraped postings (optional next)

O*NET is not a job board — it answers “what kinds of work fit?” Layer B (live search) stays DuckDuckGo/scrape.

## Alternatives / complements

| Source | When to consider |
|--------|------------------|
| ESCO (EU) | Multilingual, skills-oriented; better if you need EU coverage |
| SOC / BLS | Coarser grouping; good for reporting, less for fine matching |
| Crosswalks | O*NET exposes crosswalks to other systems — useful mapping scraped titles → SOC |

For a US-first MVP, O*NET + curated role_families is the recommended stack. ESCO matters if you go international.

## Known limitations (plan for them)

1. Title gap — “Solutions Engineer”, “RevOps”, “Developer Experience” may only appear as alternate titles or not at all → curated overlay required.
2. Generic clusters — without curated families, embeddings may over-index on “Software Developer” → the pass/fail test in next-steps.md still applies.
3. Attribution — O*NET requires credit/link in public apps (see https://services.onetcenter.org/about).
4. Not a ranking oracle — similarity suggests families; avoid_terms, constraints, and Layer C still do the filtering.

## Smallest sensible first step

Before touching the live pipeline:

1. Register for O*NET Web Services (or download one DB release).
2. Pull ~30 occupations relevant to career-changer fixtures (Software Developers, Computer Systems Analysts, Management Analysts, etc.) plus a few non-tech controls.
3. Build embedding text from description + work activities.
4. Run offline: career-changer profile vs corpus → inspect top-10.
5. Compare to the hand-written career-changer-role-family-plan.json fixture — if they agree, wire Layer A; if not, fix embedding input or add curated rows.

That validates “what to point embeddings at” without committing to API-in-the-hot-path.

## Bottom line

O*NET (or ESCO) is the right stable semantic index for Layer A. Use bulk/cached data for embeddings, API mainly for title crosswalk and exploration. Keep curated role families as the market-relevant layer on top — O*NET alone won’t give you “Platform Engineer” fidelity.

## Related docs

- docs/v0.2.0/aptitude_refinement/next-steps.md
- docs/v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md
- docs/aptitude-embedding-summary.md
