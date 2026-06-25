# O*NET design thread

Continuous notes from a June 2026 conversation on using O*NET in aptitude-search: project fit, what the dataset provides, proposed implementation steps, and the local MySQL dump layout.

Related: `[onet-and-occupation-taxonomies.md](./onet-and-occupation-taxonomies.md)` (integration plan), `[aptitude-embedding-summary.md](./aptitude-embedding-summary.md)` (semantic matching direction), `[onet_NOTES.md](./onet_NOTES.md)` (links and intro).

---

## 1. O*NET in this project todays

**Documented, not implemented.** The repo has a clear plan in `onet-and-occupation-taxonomies.md`; there is no O*NET code, config, or committed `data/` corpus yet (`data/`* is gitignored). The changelog calls this out explicitly.

### Intended role

O*NET is meant for **aptitude-to-jobtype matching** — matching aptitudes derived from the resume to job types, not live job postings.

- **Stage 1** produces an aptitude profile.
- **Aptitude-to-jobtype matching** (planned): embed profile vs a stable occupation index (O*NET + curated `role_family` descriptions).
- **Stage 2** uses those matches to drive `search_terms` / `role_family_plan`.
- **Stage 3** stays as-is: web search for live postings.

O*NET answers “what kinds of work fit?” Job discovery answers “what’s open right now?”

### Why the docs favor it

~1,000 normalized SOC occupations with summaries, work activities, alternate titles — good for explainable, career-adjacent matching. Weak on market titles (“Staff Platform Engineer”), so the plan is **O*NET bootstrap + curated role families on top**.

### Integration paths

1. **Bulk download** → ETL → static corpus + precomputed embeddings (recommended for pipeline latency).
2. **Web Services API** → mainly for title crosswalk / exploration, not embedding every run.

### What exists in code today

- `**role_family_plan*`* is real: LLM-generated in Stage 2, used in discovery query planning and fit scoring (`aptitude_fit.py`, `discovery.py`).
- No O*NET API key in config, no occupation data store, no embedding index.

Discovery does not search O*NET directly. It searches the **web** using short hiring-shaped strings built from `search_terms` on the role family plan (`backend/app/job_discovery/discovery.py`). O*NET embeddings sit **upstream**: aptitude profile → vector match → occupation titles / alternate titles → those become (or feed) `search_terms` → existing Stage 3 runs unchanged.

---

## 2. What O*NET provides

O*NET (Occupational Information Network) is a **US government occupational research database** — not a job board, not live hiring data. It describes ~1,000 standardized occupations and what work in each one typically involves.


|              |                                                                           |
| ------------ | ------------------------------------------------------------------------- |
| **Sponsor**  | US Dept. of Labor (ETA)                                                   |
| **Purpose**  | Shared vocabulary for describing jobs, workers, and labor-market context  |
| **Taxonomy** | **O*NET-SOC** — roughly **1,016 occupations** (current release: **30.3**) |
| **Updates**  | Quarterly data refreshes; major content-model changes periodically        |
| **License**  | Bulk database is **CC BY 4.0** (free to use with attribution)             |


Think of it as a **structured encyclopedia of occupations**, not a feed of open roles.

Official overview: [O*NET Content Model](https://www.onetcenter.org/content.html) · Database: [O*NET 30.3 Database](https://www.onetcenter.org/database.html)

### Mental model: Worker → Job → Market


| Dimension  | What it covers                                          |
| ---------- | ------------------------------------------------------- |
| **Worker** | Traits, requirements, experience needed to do the work  |
| **Job**    | What the work actually involves day-to-day              |
| **Market** | Wages, outlook, demand (lighter than BLS in some areas) |


Everything hangs off the **Content Model** — a hierarchy of variables with definitions, scales, and occupation-level ratings.

### The occupation spine

Every row is keyed by **O*NET-SOC code** (e.g. `15-1252.00` = Software Developers).

Per occupation:

- **Official title + description**
- **Alternate / lay titles** (~57k mappings)
- **Related occupations** (10 primary + 10 supplemental)
- **Job Zone** (1–5: prep level)

### About the worker

- **Abilities** (~52): reasoning, verbal, spatial, dexterity — importance/level per occupation
- **Skills**: Essential (~~10), Transferable (~~25), Software (~8,750 tools; Hot Technologies, In Demand flags)
- **Knowledge** (~33 domains)
- **Education & experience**: typical level, certifications, apprenticeship, OJT
- **Career interests**: RIASEC + 41 specific interest areas (new in 30.x)
- **Work styles** (~21): adaptability, attention to detail, innovation, etc.

### About the job

- **Tasks** (~19k statements, ~162k ratings): concrete duty statements
- **Work activities** (hierarchical): GWA → IWA → DWA (~2,087 detailed activities). **Richest signal for aptitude-style matching.**
- **Work context** (~298k ratings): environment, pace, autonomy, contact with others
- **Emerging tasks**: proposed future tasks (weak forward-looking signal)

### Linkages & crosswalks

Relationship tables connect abilities, skills, and work styles to work activities and work context. **Crosswalks** map O*NET-SOC to SOC, DOT, military MOS, ESCO, education programs, Occupational Outlook Handbook, etc.

### Access paths

1. **Bulk download** — tab-delimited, Excel, or SQL (MySQL/PostgreSQL/SQL Server)
2. **Web Services API** — [services.onetcenter.org](https://services.onetcenter.org/), JSON REST, always current DB
3. **Human-facing sites** — O*NET OnLine, My Next Move
4. **Machine-readable taxonomies** — JSON-LD competency frameworks (CTDL/ASN)

### Scale (release 30.3)


| Asset                   | Approx. size |
| ----------------------- | ------------ |
| Occupations             | ~1,016       |
| Job/alternate titles    | ~57,000      |
| Task statements         | ~19,000      |
| Work activity ratings   | ~73,000      |
| Software skill linkages | ~31,800      |


Large relationally, **small as a search index** (~1k embeddable documents).

### Fit for aptitude-search

**Good for:** stable aptitude-to-jobtype matching index, explainable matches, career-adjacent discovery, title normalization, finite embed-once corpus.

**Not good for (alone):** live job listings, market-granular titles (“RevOps”, “DevEx”), ranking oracle without filtering, raw skills/abilities tables as primary embedding input (recreates keyword search in vector form).

**Recommended embedding input** — one narrative doc per occupation:

```text
Title: Software Developers
Summary: [O*NET description]
Work activities: [top N by importance, as prose]
Alternate titles: [sample from Job Titles]
```

Weight work activities + description over raw Skills/Abilities tables. Aligns with aptitude side (`strengths`, `working_style_signals`) rather than `core_skills`.

### Known limitations

1. **Title gap** — market titles may be missing or only alternate titles → curated overlay required
2. **Generic clusters** — may over-index on “Software Developer” without curated families
3. **Attribution** — required in public apps ([services.onetcenter.org/about](https://services.onetcenter.org/about))
4. **Not a ranking oracle** — similarity suggests families; `avoid_terms`, constraints, posting fit ranking still filter

---

## 3. Proposed next steps and feedback

### Stated plan

1. Pull data down locally
2. Build a vector database
3. Figure out what to embed (first guess: Abilities)
4. Refactor discovery queries to use embedded data
5. Use discovery query results to run existing search / discovery

### Adjusted sequence


| Step                       | Verdict                                                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Pull data locally          | ✓ Start here — bulk download or local MySQL dump                                                                 |
| Vector database            | ✓ But ~1,016 occupations is tiny; precomputed vectors + in-process cosine may suffice for v1                     |
| Embed Abilities            | **→ Prefer occupation narrative** (description + work activities + titles), not Abilities table                  |
| Refactor discovery queries | **→ Add aptitude-to-jobtype matcher; feed `role_family_plan.search_terms`** — `discovery.py` may need no changes |
| Run existing search        | ✓ Already wired — no work on Stage 3 machinery                                                                   |


Add **step 0: offline spike** before production wiring — ~30 occupations, embed, run career-changer profile, inspect top-10 vs fixture.

### What to embed (not Abilities first)

Project docs:

> Don’t embed skill checklists alone — that recreates keyword search in vector form.  
> Weight work activities + description higher than raw Skills tables.

**Abilities** in O*NET are occupation *requirement ratings* (`Oral Comprehension`, `Deductive Reasoning`), not a narrative of what the work is like. They align poorly with Stage 1 output (`strengths`, `working_style_signals`, `adjacent_roles`).

Embed **aptitude profile side** similarly — strengths + working_style_signals + adjacent_roles as prose, not `core_skills`.

Abilities / work styles / RIASEC are useful **later** as structured filters or explainability, not as primary embedding payload.

### Where code changes actually land

```
Stage 1 aptitude profile
  → embed profile
  → vector search O*NET corpus
  → top-K occupations + alternate titles
Stage 2 role family plan (augment LLM with O*NET matches, or replace search_terms source)
Stage 3 discovery (unchanged)
```

**Recommended placement:** aptitude-to-jobtype matching between Stage 1 and 2.

**Option B:** Map top O*NET matches directly to `search_terms` via alternate titles; faster prototype; loses `work_modes` / `avoid_terms` unless added separately.

Stage 2 today also produces `work_modes`, `avoid_terms`, and `fit_reason` — used by `aptitude_fit.py`. Pragmatic path: **O*NET drives `search_terms`; keep Stage 2 (or lighter rules) for work_modes/avoid_terms** until embedding corpus is validated.

### Minimal files for first ETL subset


| File (tab or SQL)                         | Why                                                  |
| ----------------------------------------- | ---------------------------------------------------- |
| Occupation Data                           | Title, SOC code, description                         |
| Work Activities + Content Model Reference | Top-rated activities per occupation (names via join) |
| Job Titles                                | Alternate/lay titles for search_terms                |
| Related Occupations                       | Adjacent-role expansion                              |


---

## 4. O*NET 30.3 MySQL dump (`data/download/db_30_3_mysql/`)

Local path (gitignored): `data/download/db_30_3_mysql/` — **45 MySQL-format SQL scripts**, ~284 MB uncompressed. Official docs: [O*NET 30.3 MySQL dictionary](https://www.onetcenter.org/dictionary/30.3/mysql/).

**Yes — each file creates one table and bulk-loads it with `INSERT` rows.** Together they are the full O*NET 30.3 relational database.

### File pattern

Every file:

1. `CREATE TABLE ...` with column types and foreign keys
2. Thousands or millions of `INSERT INTO ... VALUES (...)` lines

Example (`03_occupation_data.sql`):

```sql
CREATE TABLE occupation_data (
  onetsoc_code CHARACTER(10) NOT NULL,
  title CHARACTER VARYING(150) NOT NULL,
  description CHARACTER VARYING(1000) NOT NULL,
  PRIMARY KEY (onetsoc_code));

INSERT INTO occupation_data (...) VALUES ('15-1252.00', 'Software Developers', '...');
```

Rating tables use a **long/narrow** shape: one row per `(occupation, element, scale)` with numeric `data_value`, joined via `element_id` and `onetsoc_code`.

### How the 45 files group


| Files     | Role                                                                     |
| --------- | ------------------------------------------------------------------------ |
| **01–11** | Reference / taxonomy — content model tree, scales, categories, job zones |
| **12–30** | Occupation × element ratings — main fact tables                          |
| **31–33** | Work-activity hierarchy — GWA → IWA → DWA, tasks → DWA                   |
| **34–37** | Occupation relationships & titles                                        |
| **38–45** | Cross-domain linkages — abilities/skills/styles → activities/context     |


### Reference tables (load first — others FK to them)


| File                               | Table                     | Purpose                                                           |
| ---------------------------------- | ------------------------- | ----------------------------------------------------------------- |
| `01_content_model_reference.sql`   | `content_model_reference` | `element_id` → name + description (Abilities, Work Activities, …) |
| `02_job_zone_reference.sql`        | `job_zone_reference`      | Job Zones 1–5 definitions                                         |
| `04_scales_reference.sql`          | `scales_reference`        | Scale codes (`IM` = Importance, `LV` = Level, …)                  |
| `05`, `06`, `07`, `09`, `10`, `11` | Category/anchor tables    | Education, training, task/context category defs                   |


### Core spine


| File                     | Table             | ~Size  | Purpose                                               |
| ------------------------ | ----------------- | ------ | ----------------------------------------------------- |
| `03_occupation_data.sql` | `occupation_data` | 348 KB | **~1,016 occupations** — SOC code, title, description |
| `21_job_zones.sql`       | `job_zones`       | 119 KB | Prep level (1–5) per occupation                       |


### Occupation rating tables

Each links `onetsoc_code` + `element_id` + `scale_id` → `data_value`:


| File                             | Content                                    |
| -------------------------------- | ------------------------------------------ |
| `12_abilities.sql`               | Natural aptitudes (~26 MB)                 |
| `13_education.sql`               | Typical education                          |
| `14_training_and_experience.sql` | OJT, apprenticeship, experience            |
| `15_career_interest_types.sql`   | RIASEC profiles                            |
| `16_specific_interest_areas.sql` | 41 finer interest areas                    |
| `22_knowledge.sql`               | Knowledge domains                          |
| `23_software_skills.sql`         | Named tools/technologies                   |
| `24_essential_skills.sql`        | Reading, critical thinking, …              |
| `25_transferable_skills.sql`     | Systems analysis, programming, …           |
| `26_task_statements.sql`         | Task text per occupation                   |
| `27_task_ratings.sql`            | **~45 MB** — frequency/importance per task |
| `28_work_activities.sql`         | Work activity ratings (~21 MB)             |
| `29_work_context.sql`            | **~91 MB** — physical/social job context   |
| `30_work_styles.sql`             | Personality-at-work traits                 |


### Hierarchy & titles


| File                               | Purpose                                   |
| ---------------------------------- | ----------------------------------------- |
| `31_gwas_to_iwas.sql`              | General → Intermediate work activities    |
| `32_gwas_to_iwas_to_dwas.sql`      | Full GWA/IWA/DWA tree                     |
| `33_tasks_to_dwas.sql`             | Maps tasks to detailed work activities    |
| `34_emerging_tasks.sql`            | Proposed future tasks                     |
| `35_related_occupations.sql`       | 10 primary + 10 supplemental related SOCs |
| `36_job_titles.sql`                | **~57k alternate/lay titles**             |
| `37_sample_of_reported_titles.sql` | Survey-reported titles                    |


### Linkage tables (38–45)

Small bridge tables (e.g. abilities ↔ work activities). Useful for explainability; not essential for first embedding corpus.

### Structural details

**Two hub keys:**

- `occupation_data.onetsoc_code` — the occupation
- `content_model_reference.element_id` — the variable

`abilities` rows store `element_id = '1.A.1.b.4'`, not “Deductive Reasoning” as text — join to `content_model_reference` for labels and definitions.

**Scales for ratings:** filter to `scale_id = 'IM'` (Importance) and take top-N by `data_value` when building narrative text.

**Load order:** reference tables + `occupation_data` before rating tables (FK constraints) if importing into MySQL/MariaDB.

### Do you need to run these as SQL?

**Not necessarily.** The same release ships tab-delimited `.txt` and other SQL dialects from [onetcenter.org/database.html](https://www.onetcenter.org/database.html). For an embedding spike, many workflows **skip MySQL** and parse TSV or extract from SQL once. MySQL is useful for ad-hoc SQL exploration; overhead if you only need a one-time JSONL corpus.

### Minimal subset for aptitude-to-jobtype matching ETL


| Priority           | SQL files             |
| ------------------ | --------------------- |
| **Must have**      | `03`, `01`, `28`      |
| **Very useful**    | `36`, `35`            |
| **Nice later**     | `26`, `30`, `15`      |
| **Skip initially** | `29`, `27`, `38`–`45` |


---

## 5. Smallest sensible first step (from project docs)

Before touching the live pipeline:

1. Register for O*NET Web Services (or use downloaded DB release in `data/download/`).
2. Pull ~30 occupations relevant to career-changer fixtures (Software Developers, Computer Systems Analysts, Management Analysts, etc.) plus non-tech controls.
3. Build embedding text from description + work activities (join `03` + `28` + `01`).
4. Run offline: career-changer profile vs corpus → inspect top-10.
5. Compare to hand-written career-changer role-family-plan fixture — if they agree, wire aptitude-to-jobtype matching; if not, fix embedding input or add curated rows.

Validates “what to point embeddings at” without API-in-the-hot-path or full 45-table import.

---

## Related docs

- `[onet-and-occupation-taxonomies.md](./onet-and-occupation-taxonomies.md)`
- `[onet-conversation-notes.md](./onet-conversation-notes.md)` — earlier snapshot of sections 1–2
- `[aptitude-embedding-summary.md](./aptitude-embedding-summary.md)`
- `[../v0.2.0/aptitude_refinement/next-steps.md](../v0.2.0/aptitude_refinement/next-steps.md)`
- `[../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md](../v0.2.0/aptitude_refinement/conversation-aptitude-matching-direction.md)`

