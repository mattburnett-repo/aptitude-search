# O*NET conversation notes

Notes from an initial design conversation (June 2026) on using O*NET in aptitude-search. Complements [`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md) (integration plan) with project context and a fuller picture of what O*NET provides.

---

## O*NET in this project today

**Documented, not implemented.** The repo has a clear plan in `onet-and-occupation-taxonomies.md`; there is no O*NET code, config, or `data/` corpus yet. The changelog calls this out explicitly.

### Intended role

O*NET is meant for **Layer A** — matching aptitude → *role semantics*, not job postings.

- **Stage 1** produces an aptitude profile.
- **Layer A** (planned): embed profile vs a stable occupation index (O*NET + curated `role_family` descriptions).
- **Stage 1.5** uses those matches to drive `search_terms` / `role_family_plan`.
- **Stage 2** stays as-is: web search for live postings.

O*NET answers “what kinds of work fit?” Job discovery answers “what’s open right now?”

### Why the docs favor it

~1,000 normalized SOC occupations with summaries, work activities, alternate titles — good for explainable, career-adjacent matching. Weak on market titles (“Staff Platform Engineer”), so the plan is **O*NET bootstrap + curated role families on top**.

### Integration paths (per project docs)

1. **Bulk download** → ETL → static corpus + precomputed embeddings (recommended for pipeline latency).
2. **Web Services API** → mainly for title crosswalk / exploration, not embedding every run.

### What exists in code today

- **`role_family_plan`** is real: LLM-generated in Stage 1.5, used in discovery query planning and fit scoring (`aptitude_fit.py`, `discovery.py`).
- No O*NET API key in config, no occupation data store, no embedding index.

### Practical takeaway

The project already has the *downstream* hook (`role_family_plan` → search). O*NET would be the *upstream* stable index to improve or augment how those families are chosen — still design-phase only.

---

## What O*NET is

O*NET (Occupational Information Network) is a **US government occupational research database** — not a job board, not live hiring data. It describes ~1,000 standardized occupations and what work in each one typically involves.

| | |
|---|---|
| **Sponsor** | US Dept. of Labor (ETA) |
| **Purpose** | Shared vocabulary for describing jobs, workers, and labor-market context |
| **Taxonomy** | **O*NET-SOC** — roughly **1,016 occupations** (current release: **30.3**) |
| **Updates** | Quarterly data refreshes; major content-model changes periodically |
| **License** | Bulk database is **CC BY 4.0** (free to use with attribution) |

Think of it as a **structured encyclopedia of occupations**, not a feed of open roles.

---

## Mental model: three dimensions

Recent releases organize everything around **Worker → Job → Market**:

| Dimension | What it covers |
|-----------|----------------|
| **Worker** | Traits, requirements, experience needed to do the work |
| **Job** | What the work actually involves day-to-day |
| **Market** | Wages, outlook, demand (lighter than BLS in some areas) |

Everything hangs off the **Content Model** — a hierarchy of variables with definitions, scales, and occupation-level ratings.

Official overview: [O*NET Content Model](https://www.onetcenter.org/content.html)

---

## The occupation spine

Every row is keyed by **O*NET-SOC code** (e.g. `15-1252.00` = Software Developers).

Per occupation you get:

- **Official title + description** (`Occupation Data` — ~1,016 rows)
- **Alternate / lay titles** (`Job Titles` — ~57k mappings; `Sample of Reported Titles` — ~8k)
- **Related occupations** (10 primary + 10 supplemental per occupation)
- **Job Zone** (1–5: prep level — little training → extensive experience/education)

This is the backbone for title crosswalks: “Solutions Engineer” → nearest SOC code.

---

## About the worker (requirements & traits)

### Abilities (~52 variables, ~93k ratings)

Innate/aptitude-style capacities: reasoning, verbal, spatial, dexterity, etc. Rated on importance/level scales per occupation.

### Skills (three tiers in 30.x)

- **Essential Skills** (~10): reading, writing, math, critical thinking, active learning…
- **Transferable Skills** (~25): coordination, systems analysis, programming, negotiation…
- **Software Skills** (~8,750 named tools): Python, Excel, Salesforce, etc. Includes **Hot Technologies** (176 tools, employer-posting derived) and **In Demand** flags per occupation.

### Knowledge (~33 domains)

Business, engineering, computers, medicine, law, etc. — importance/level per occupation.

### Education & experience

Typical education level, certifications, apprenticeship, on-the-job training, subject-area requirements.

### Career interests

- **RIASEC types** (Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
- **41 specific interest areas** (new in 30.x — e.g. Information Technology, Engineering, Finance)

### Work styles (~21)

Personality-at-work traits: adaptability, attention to detail, innovation, stress tolerance, etc.

---

## About the job (what work looks like)

### Tasks (~19k statements, ~162k ratings)

Concrete duty statements (“Write code…”, “Analyze user needs…”) with frequency/importance ratings.

### Work activities (hierarchical)

Three levels of granularity:

- **General Work Activities (GWA)** — broad (e.g. “Analyzing Data or Information”)
- **Intermediate (IWA)**
- **Detailed (DWA)** — ~2,087 specific activities

Tasks link to DWAs, so you can reason at task level or roll up to generalized patterns. **This is the richest signal for aptitude-style matching** in the project docs.

### Work context (~298k ratings)

Environmental/situational factors: indoors/outdoors, pace, autonomy, contact with others, consequences of error, etc.

### Emerging tasks

Proposed new/revised tasks not yet fully collected — a weak signal for “where occupations are heading.”

---

## Linkages & crosswalks

O*NET also ships **relationship tables** connecting domains:

- Abilities ↔ work activities / work context
- Skills ↔ work activities / work context
- Work styles ↔ work activities / work context

**Crosswalks** map O*NET-SOC to other systems: SOC, DOT, military MOS, ESCO, education programs, Occupational Outlook Handbook, etc.

Useful when you scrape a posting title and need a stable occupation ID.

---

## How you can access it

### 1. Bulk download (45 core files)

Tab-delimited, Excel, or SQL dumps from [O*NET Database](https://www.onetcenter.org/database.html).

Best for: building a local corpus, precomputing embeddings, versioning in `data/`.

### 2. Web Services API (free, API key)

[services.onetcenter.org](https://services.onetcenter.org/) — JSON REST, OpenAPI spec, always current DB.

Includes:

- Full database table access (list tables → columns → rows)
- Occupation reports (summary/details/custom)
- Keyword search, browse by job family/zone/industry/technology
- Crosswalk searches
- Interest Profiler, career-cluster browsing (My Next Move surfaces)

Best for: prototyping, title lookup, exploration — not high-volume pipeline hot path.

### 3. Human-facing sites

O*NET OnLine, My Next Move, etc. — same underlying data, UI-oriented.

### 4. Machine-readable taxonomies

JSON-LD competency frameworks (CTDL/ASN schema) for occupations and skill hierarchies.

---

## Scale at a glance (release 30.3)

| Asset | Approx. size |
|-------|----------------|
| Occupations | ~1,016 |
| Job/alternate titles | ~57,000 |
| Task statements | ~19,000 |
| Work activity ratings | ~73,000 |
| Software skill linkages | ~31,800 |
| Knowledge ratings | ~59,000 |
| Ability ratings | ~93,000 |

It’s **large in relational terms**, but **small as a search index** (~1k embeddable documents).

---

## Fit for aptitude-search

### Good for

- Stable **“other side”** for aptitude → role matching (Layer A)
- **Explainable** matches (“aligned with work activities X, Y”)
- **Career-adjacent** discovery across industries, not just tech
- **Title normalization** for scraped job postings
- **Finite corpus** — easy to embed once and version

### Not good for (alone)

- Current job listings, company-specific salaries, or real-time hiring demand
- Granular market titles (“Staff Platform Engineer”, “RevOps”, “DevEx”)
- A ranking oracle — similarity suggests families; filtering still needed
- Skills/tech tables used alone — skew toward keyword matching (embed skill checklists by themselves and you recreate keyword search in vector form)

### Recommended embedding input (from project docs)

Per occupation, build narrative text — not raw skill tables:

```text
Title: Software Developers
Summary: [O*NET description]
Work activities: [top N activities as prose]
Typical context: [technology design, systems analysis, ...]
Alternate titles: [...]
```

Weight work activities + description higher than raw Skills tables. Aligns with aptitude side (strengths, working_style_signals) rather than core_skills.

### Practical pattern

Bulk download → ETL → `data/occupations/onet_corpus.jsonl` → precomputed embeddings → cosine search offline or in-process. Keep curated `role_family` rows on top for market fidelity.

---

## Known limitations (plan for them)

1. **Title gap** — “Solutions Engineer”, “RevOps”, “Developer Experience” may only appear as alternate titles or not at all → curated overlay required.
2. **Generic clusters** — without curated families, embeddings may over-index on “Software Developer”.
3. **Attribution** — O*NET requires credit/link in public apps ([services.onetcenter.org/about](https://services.onetcenter.org/about)).
4. **Not a ranking oracle** — similarity suggests families; `avoid_terms`, constraints, and Layer C still do the filtering.

---

## Smallest sensible first step (from project docs)

Before touching the live pipeline:

1. Register for O*NET Web Services (or download one DB release).
2. Pull ~30 occupations relevant to career-changer fixtures (Software Developers, Computer Systems Analysts, Management Analysts, etc.) plus a few non-tech controls.
3. Build embedding text from description + work activities.
4. Run offline: career-changer profile vs corpus → inspect top-10.
5. Compare to the hand-written career-changer-role-family-plan fixture — if they agree, wire Layer A; if not, fix embedding input or add curated rows.

That validates “what to point embeddings at” without committing to API-in-the-hot-path.

---

## Related docs

- [`onet-and-occupation-taxonomies.md`](./onet-and-occupation-taxonomies.md) — Layer A integration plan
- [`aptitude-embedding-summary.md`](./aptitude-embedding-summary.md) — semantic matching direction
- [`../v0.2.0/aptitude_refinement/next-steps.md`](../v0.2.0/aptitude_refinement/next-steps.md)
- [`../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md`](../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md)
