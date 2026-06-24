# Conversation: Resume → Aptitude → Job Discovery (and beyond keyword search)

Saved from a project chat session. Continuous markdown; code and diagrams are inline (no fenced blocks).

---

## User

Describe, briefly and in simple terms, how this project turns a resume into a set of job openings. Focus on clarifying how the resume gets converted to a collection of aptitudes, and how those aptitudes are used to search for job openings.

---

## Assistant

The project runs a **two-stage pipeline** when you call `POST /v1/pipeline`: first it turns the resume into a structured aptitude profile, then it uses that profile to search the web and return verified job openings.

### Stage 1: Resume → aptitude profile

The resume text is sent to an LLM with a strict prompt (`prompts/01-resume-to-aptitude-profile.md`). The model does **not** search for jobs — it only **extracts and organizes** what the resume actually shows.

The output is a JSON **AptitudeProfile** with fields like:

- **core_skills** — main technologies/capabilities used repeatedly (e.g. TypeScript, React)
- **secondary_skills** — real but less central skills
- **strengths** — work patterns (ownership, mentoring), not tools
- **adjacent_roles** — realistic next roles the person could move into
- **seniority_band** — entry / mid / senior / etc.
- **domains**, **working_style_signals**, plus a short **aptitude_summary**

Each item gets a **confidence** level (high/medium/low) tied to resume evidence. The API validates this JSON against a schema before moving on.

So “aptitudes” here means a **structured career signal profile** — skills, level, strengths, and plausible roles — not a simple keyword list.

### Stage 2: Aptitude profile → job openings

Stage 2 has two parts:

**2a — Web search (Python, no LLM for query planning)**

The code reads the aptitude profile and optional **constraints** (location, remote preference, salary, industries) and builds search queries like:

    senior software engineer TypeScript Toronto remote jobs

Queries are built from:

- **seniority_band** → a role label (e.g. “senior software engineer”)
- **core_skills** (up to ~6 queries; **secondary_skills** fill in if needed)
- **constraints** → location and remote/hybrid/onsite

For each query, it runs **`search_job_postings`**: DuckDuckGo search → filter to job-like URLs → scrape posting pages. That produces a raw **`found_jobs`** list.

**2b — Synthesis (LLM)**

A second LLM call takes the aptitude profile, constraints, and `found_jobs`, and produces **`verified_matches`**: a curated list of openings with match explanations. It **does not invent URLs** — every result must come from what was actually found in the search. The API also filters out any URL that wasn’t observed during search.

### End result

You get back:

1. **`aptitude_profile`** — what the system inferred from the resume
2. **`verified_matches`** — real job postings found on the web, ranked and explained against that profile

In short: the resume becomes a **structured aptitude map** via LLM extraction; those skills and seniority drive **web search queries**; search results are then **verified and matched** back to the profile before being returned.

---

## User

So it looks like all this thing does is reads a resume, extracts keywords and then runs searches with those keywords.

---

## Assistant

You're mostly right about what it **actually does today**, with a few caveats.

**The search step is keyword search.** Stage 2 builds queries like `senior software engineer TypeScript Toronto remote jobs` from:

- skill **names** from `core_skills` (and `secondary_skills` if needed)
- `seniority_band` → a role label
- location / remote from constraints

It then runs those through DuckDuckGo, filters job-like URLs, scrapes pages, and collects results. There is no embedding search, no semantic ranking over postings, and no vector DB.

**Stage 1 is more than “grab keywords,” but not by much for search purposes.** The LLM produces a structured profile — skills with confidence and resume evidence, strengths, adjacent roles, domains, a summary, etc. That’s richer than a bag of words. But the **discovery code only uses a thin slice of it**: skill names, seniority, and location/remote. Fields like `strengths`, `adjacent_roles`, `domains`, and `industries_include` / `salary_min` do **not** change what gets searched; they mostly feed the later synthesis step (or show up in the written `search_plan`).

**What the second LLM call adds:** it takes the scraped `found_jobs` plus the full profile and constraints, then picks/explains matches, applies diversification rules (max per company, etc.), and drops any URL that wasn’t actually found in search. So the value after search is curation and explanation, not a fundamentally different matching engine.

The project’s own docs describe the **intended direction** as aptitude → role families → targeted discovery, and explicitly say embeddings/semantic search are **not** the current implementation — more like an exploratory layer to figure out what signals matter.

**Bottom line:** resume → LLM extracts structured skills (and other signals) → those skill names drive web keyword searches → another LLM tidies and explains the results. The “aptitude-driven” framing is real in the **profile model** and **synthesis**, but the **discovery mechanism** is still essentially smart keyword extraction + search. Your read is fair.

---

## User

So it's just a fancy keyword generator.

---

## Assistant

That's a fair summary of what it does **right now**.

The LLM in Stage 1 is a structured keyword (and metadata) generator: it normalizes skill names, guesses seniority, and fills in extra fields the search step mostly ignores. Stage 2 turns those into Google-style queries, scrapes what comes back, and a second LLM filters and writes match blurbs.

The “fancy” parts are the schema, evidence/confidence fields, URL verification, and explanation layer — not a different kind of job matching. The docs even describe semantic/aptitude matching as direction, not current behavior.

So: **fancy, structured keyword generator + web search + LLM cleanup** — not wrong.

---

## User

That's not very useful.

---

## Assistant

You're right to be skeptical about the **incremental value** today.

If someone can already search `senior TypeScript remote Toronto jobs`, this pipeline mostly automates that: LLM pulls skill names from the resume, runs a few similar queries, scrapes results, and writes explanations. That's convenient, but not a step change over typing keywords into Google or a job board.

Where it **does** help a little:

- Normalizes messy resume wording into consistent skill names
- Bundles search + scrape + a structured response in one API call
- Tries to drop bad links and explain why a posting might fit

Where it **doesn't** help much yet:

- It doesn't find roles you wouldn't think to search for (`adjacent_roles` aren't used in search)
- Industry/salary constraints don't drive discovery
- No real aptitude matching — just keyword overlap plus LLM narration
- Web search quality is noisy and capped (~6 queries per run)

So as a **product**, it's more of a prototype or demo of "resume in → jobs out" than something that clearly beats manual search. The project's own docs treat richer matching as **future direction**, not what ships now.

If the goal is genuinely useful job discovery, the gap is in **what gets searched** (role families, not just skill tokens) and **how results are ranked** (fit to work patterns, not keyword overlap) — not another layer of keyword polish.

If you want to push it somewhere useful, say what you care about most (better discovery, better ranking, or something else) and we can sketch what would actually need to change.

---

## User

We need to move this past the "automated keyword generator / search machine" stage. It doesn't really do anything with actual aptitude(s).

You wrote:

"If the goal is genuinely useful job discovery, the gap is in what gets searched (role families, not just skill tokens) and how results are ranked (fit to work patterns, not keyword overlap) — not another layer of keyword polish."

That's close to what I'm thinking.

---

## Assistant

You're pointing at the real gap: **Stage 1 already produces aptitude-shaped signals, but Stage 2 mostly ignores them.** The career-changer fixture is a good example — it surfaces modernization, integration-heavy work, logistics/nonprofit domains, and adjacent roles like Solutions Engineer and Platform Engineer. Today's discovery would still turn that into `senior software engineer Python jobs`, `senior software engineer Django jobs`, etc.

`docs/aptitude-embedding-summary.md` describes the direction you want; the code just hasn't caught up.

### The shift

Move from:

    resume → skill names → keyword search → LLM explains results

To:

    resume → aptitude profile → role families / work modes → targeted search → role-vs-aptitude fit ranking

"Aptitude" should mean **what kind of work someone is suited for**, not which tools they've used. Skills still matter, but as supporting evidence — not as the search driver.

### What to add (concretely)

**1. A new middle artifact: role-family plan**

Between profile and search, produce something like what `aptitude-embedding-summary.md` sketches:

- **3–5 role families** the person plausibly fits (from `adjacent_roles`, `strengths`, `domains`, `working_style_signals`, `aptitude_summary`)
- Per family: **work modes** (e.g. "integration design", "legacy migration", "stakeholder coordination")
- **search_terms** — actual job titles to query, not tech stack tokens
- **avoid_terms** — obvious misfits (quota sales, pure research, etc.)
- **fit_reason** tied to profile evidence

For the career-changer resume, you'd want searches aimed at things like "solutions engineer integrations", "platform engineer internal tools", "implementation engineer" — not six variations on Python.

This can be an LLM step with a new schema. It doesn't require embeddings on day one.

**2. Discovery driven by role families, not core_skills**

Replace `build_discovery_queries()`'s skill loop with queries built from:

- `search_terms` from the role-family plan
- `seniority_band`
- constraints (location, remote)
- optionally 1–2 **domain** tokens (logistics, nonprofit) where relevant

`core_skills` become context for ranking and explanation, not the primary query source. That's the biggest behavioral change.

**3. Extract a role profile from each posting (not just title + URL)**

When you scrape a job page, add a lightweight extraction step that pulls:

- **Responsibilities** ("what you'll do") vs **requirements** ("what you need")
- Inferred **work modes** (build vs maintain, customer-facing vs internal, greenfield vs ops)
- Domain, seniority, employment type

The doc already calls out that responsibilities reveal role semantics better than requirement bullet lists. Right now you're mostly matching on titles and snippets.

**4. Rank on aptitude fit, not keyword overlap**

Before synthesis (or as input to it), score each `found_job` against the aptitude profile on dimensions you already have:

| Aptitude signal | Match against |
|-----------------|---------------|
| strengths | Posting responsibilities / work patterns |
| working_style_signals | Ambiguity, ownership, collaboration in posting |
| domains | Company/product domain |
| adjacent_roles | Title + responsibility alignment |
| core_skills | Requirements (lowest weight — table stakes) |

Output structured `match_signals` and `confidence` (the schema already has fields for these). Synthesis becomes **formatting and narrating pre-ranked fits**, not inventing why a React job "matches" because the resume says React.

**5. Constraints that actually constrain**

`industries_include` / `exclude` and `salary_min` are in constraints today but barely affect discovery. Wire them into:

- query terms or post-search filtering
- hard excludes in ranking (gambling, etc.)

Otherwise "aptitude + constraints" is mostly cosmetic.

### Smallest useful increment

If you want one change that proves the concept without rebuilding everything:

**Add Stage 1.5 (role-family plan) and switch discovery to use its `search_terms`.**

Keep synthesis as-is initially. Compare runs on the same resume:

- Old: skill-keyword queries
- New: role-family queries

Success = postings the candidate wouldn't have searched manually, with titles aligned to `adjacent_roles` / `strengths`, not just their stack.

The career-changer fixture is a good golden test: if results are all "Senior Full Stack Engineer" with Python/Django, you haven't moved. If you get integration/platform/solutions-style roles grounded in modernization and logistics, you have.

### What "useful" looks like

Judge it on outcomes the keyword machine can't hit:

- Surfaces **non-obvious but justified** roles (from `adjacent_roles`)
- Explains fit via **work patterns** ("thrives in transitional environments") not tool lists
- **Filters** generic SWE postings that share keywords but wrong work mode
- Stays explainable — every match cites profile evidence, not vibes

### What to avoid (for now)

- **More prompt polish on synthesis** without changing what gets searched — that's lipstick on the keyword machine
- **Jumping straight to embeddings/vector DB** — your own doc is right that comparability and ontology matter first; vectors are optional later
- **Expanding Stage 1 forever** — the profile is already rich enough; the bottleneck is downstream usage

---

The product story becomes honest: aptitude isn't "we extracted better keywords." It's **infer what kinds of work fit this person → search within those families → rank by work-pattern fit.**

---

## User

The ideal solution would embed the aptitude(s) and then do a vector search using those embedded values. The problem / current unknown is "what to point those embeddings at?"

---

## Assistant

You're right that embeddings are only half the problem. An aptitude vector is useless until you define **a stable, comparable thing on the other side of the search**.

### The real question

It's not "should we embed aptitudes?" — it's:

**What is the retrieval corpus, and what text/object gets embedded for each item in it?**

If both sides aren't describing **the same kind of thing** (work mode, role semantics, occupational family), vector search just finds statistically similar wording, which is keyword search with extra steps.

### Options for what to point at

| Target | What you embed | Pros | Cons |
|--------|----------------|------|------|
| Raw job postings | Full scraped JD text | Direct: compare person → opening | Huge, noisy, stale index; inflated reqs; same title ≠ same work; you don't own a job corpus |
| Extracted role profiles | LLM-parsed responsibilities, work modes, seniority from each posting | Closer to "what work is this?" | Still per-posting; best as **re-rank** after discovery, not primary index |
| Role-family archetypes | Curated descriptions: "Solutions Engineer (integration-heavy SaaS)" with work modes | Small stable index; interpretable; drives non-obvious discovery | Needs ontology curation; abstraction can miss edge cases |
| O*NET / ESCO occupations | Official occupation summaries + work activities | Normalized, broad (not just tech), finite | Generic; lags market titles; "Staff Platform Engineer" won't map cleanly |
| Per-candidate role hypotheses | Dynamic docs generated from aptitude profile: "person suited for X because Y" | Personalized retrieval targets; no global index | Not a fixed corpus — more like **query expansion** than search |
| Company/team context | Product domain + team charter + title | Disambiguates "Engineer" at a logistics co vs fintech | Hard to get at scale; secondary signal |

Your own doc already lands on the same split: job text + LLM extraction + optional taxonomy normalization — not "embed the whole internet."

### A practical architecture (layered)

Don't pick one target. Use **three layers**, each with a different corpus:

    Layer A — "What kinds of work fit this person?"
      Embed: aptitude profile (summary + strengths + work modes + domains)
      Search against: role-family archetypes + O*NET occupations (small, stable index)
      Output: top-K role families / occupations + explainable scores

    Layer B — "Find live openings in those families"
      Not vector search — targeted keyword/search API using family-specific titles
      (vector search is bad at freshness; job boards are)

    Layer C — "Which of these postings actually fit?"
      Embed: extracted role profile per posting (responsibilities-first, not req laundry list)
      Compare to aptitude embedding(s)
      Re-rank found_jobs before returning

Layer A answers your unknown: **point aptitude embeddings at role semantics, not at job postings.**

Layer C answers "which of these 40 scraped results matter?" — a small, per-run vector compare is cheap and high-value.

Trying to skip A and C and build a global posting index is usually where job-matching startups burn time.

### What to embed on the aptitude side

Don't embed `core_skills` as a bag of tokens — that's the keyword trap in vector form.

Better inputs (can be one doc or multiple vectors):

- `aptitude_summary`
- `strengths` + `working_style_signals` (work patterns)
- `domains`
- `adjacent_roles` with evidence

Skills get **lower weight** or a separate "table stakes" channel so React doesn't dominate over "thrives in modernization under ambiguity."

Multi-vector fusion (strengths vs skills vs domains) often beats one blob — lets you say *why* something matched.

### What to embed on the role side (the corpus)

For a **stable index** (Layer A), each item should look like the role-family JSON in `aptitude-embedding-summary.md`:

    role_family: Solutions / Implementation (integration-heavy)
    work_modes: customer integrations, API design, technical discovery
    typical_titles: Solutions Engineer, Implementation Engineer, Integration Engineer
    not_this: quota-carrying sales, pure SRE on-call rotation

Embed the narrative + work_modes + typical responsibilities — **not** a skill checklist.

O*NET gives you ~1,000 occupations for free as a bootstrap corpus. Your curated role families sit on top for market-relevant granularity (Platform Engineer, RevOps, etc.).

For **per-posting** compare (Layer C), embed extracted:

- Responsibilities / outcomes
- Collaboration pattern
- Domain
- Seniority

…and downweight or omit the requirements section.

### Why "point at postings" alone fails

- **Title collision**: "Software Engineer" spans 10 work modes
- **Requirement inflation**: every posting wants Kubernetes
- **Freshness**: embeddings of stale postings rot
- **No training signal**: you don't have hire/reject labels to learn a custom space

So vector search over a live posting index without normalization is usually worse than it sounds.

### The validation question (before building infra)

From your doc — still the right test:

> Can aptitude signals identify role families that produce **better discovery** than skill keywords alone?

You can test Layer A **without** a vector DB:

1. Take 20–50 hand-curated role-family descriptions (+ O*NET samples)
2. Embed aptitude profiles from your fixtures
3. See if top matches align with human judgment on `adjacent_roles` / `strengths`

If career-changer ranks "Solutions Engineer / Platform / modernization TPM" above "Senior Python Developer," the target corpus is right. If everything clusters on "Software Developer," your archetypes or aptitude embedding input is wrong.

### Bottom line

**Point aptitude embeddings at role semantics** — curated role families + occupation taxonomies — not raw job postings.

Use vectors to answer: *"What kinds of work is this person suited for?"*

Use search (keyword/API) to answer: *"What's open right now in those families?"*

Use a second vector compare to answer: *"Of what we found, which postings actually match the work mode?"*

That keeps embeddings where they're strong (semantic similarity of **work**) and avoids pretending you have a maintained global job embedding index.

---

## User

Save this entire chat in continuous / unfenced markdown format to the project folder `docs`.

---

*End of saved conversation.*
