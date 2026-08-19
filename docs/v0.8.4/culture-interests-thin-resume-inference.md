# Inferring culture preferences and interests from thin resumes

How Stage 1 should extract `culture_preferences` and `interests` when the resume does not state them, or only provides partial evidence. Complements `stage1-prompt-revision-plan.md`. Prompt-only proposal — no schema changes.

## Framing

Most resumes look like a skills/title CV (e.g. `fixtures/sample-resumes/senior-backend-engineer.txt`): no Interests section, no “I prefer startups.” Halo signals must come from **proxy patterns**, labeled carefully and confidence-capped.

Treat extraction as evidence tiers:

| Tier | What it looks like | Confidence | Example |
|------|--------------------|------------|---------|
| **Stated** | Explicit preference/passion | `high` | “Happiest in lean teams… Drawn to climate…” |
| **Chosen** | Elective behavior when they had options | `medium` | Volunteer civic hack nights; climate side project |
| **Patterned** | Repeated employer/role *setting*, not one job | `medium` or `low` | 2+ lean/nonprofit stints → lean / mission-driven |
| **Incidental** | Single employer industry only | usually **omit** (or `domains` only) | One logistics job ≠ interest in logistics |

`[]` stays valid when the resume is pure skills/titles with no repeated environment and no elective subject signal — e.g. a thin backend CV may yield **culture from employer pattern** but **empty interests**.

---

## `culture_preferences` without explicit statements

Infer **environment fit from history**, not wishes.

### Proxy sources (strongest first)

1. **Employer type sequence** — startup / Series B, nonprofit, agency, bank/fintech, gov, big-corp process org
2. **Org constraints in bullets** — “tight budgets,” “no dedicated PM,” “grant cycles,” “dedicated QA,” “SLO ownership”
3. **Team size / ownership shape** — small eng team, end-to-end ownership vs feature team with PM/QA
4. **Tenure patterns** — repeated return to the same *kind* of org (stronger than one stint)

### Label as environment adjectives, not “wants X”

- Repeated lean / no-PM / tight budget → `resource-constrained / lean` (`medium`)
- Nonprofit + civic + grant language → `mission-driven / nonprofit` (`medium`)
- Fintech + banking + SLOs + regulated money path → `regulated enterprise` / `reliability-critical` (`medium`/`low`)
- One process-heavy SaaS stint only → weak; prefer `[]` or `low` unless repeated

### Partial evidence rule

- One strong org-context clue → at most **one** `low`/`medium` item with a short `evidence_from_resume` quote
- Two independent clues (employer type + bullet constraint) → `medium` is OK
- Never `high` unless they state preference

### Do not infer

Remote, salary, location, or personality (“collaborative person”) from culture proxies.

---

## `interests` without explicit statements

Interests need a **subject they sought**, not where payroll put them.

### Proxy sources (strong → weak)

1. Volunteer / community / mentorship themes outside the day job
2. Side projects / OSS with a topical theme (climate, education, games)
3. Stated summary language (“drawn to…”)
4. Elective education or consistent *optional* domain choice across roles when alternatives existed

### Partial evidence rule

- Side project *or* volunteer on topic T → one interest at `medium`/`low`
- Work domain only (logistics employer, fintech employer) → **`domains`**, not `interests`
- Same subject in work **and** elective volunteer/side project → stronger interest (`medium`), still not `high` unless stated
- Pure skills resume with no elective subject → **`interests: []`** is correct

Empty interests on keyword-only engineering CVs is expected — not a failure.

---

## Separating the two fields under ambiguity

| Resume cue | Prefer field |
|------------|----------------|
| Nonprofit / lean / regulated / startup *as workplace* | `culture_preferences` |
| Climate / civic / games / healthcare *as topic* | `interests` |
| “Owned discovery with no PM” | `working_style_signals` (and maybe lean culture) |
| “Worked in logistics” alone | `domains` only |

**Rich example:** `civic-climate-product-engineer.txt` — culture from lean/nonprofit/startup **and** interests from volunteer/side project/summary.

**Thin example:** `senior-backend-engineer.txt` — culture from fintech/reliability pattern; interests likely `[]`.

---

## Prompt mechanics to encode

1. **Halo pass after facts:** for culture, ask “what *kinds of workplaces* recur?”; for interests, ask “what *subjects* appear outside mandatory employment?”
2. **Confidence caps:** stated → `high`; multi-proxy pattern → `medium`; single thin proxy → `low` or omit.
3. **Require `evidence_from_resume`** on every inferred culture/interest item (forces grounding).
4. **Partial is OK:** 0–2 items beats a padded list; never invent hobbies.
5. **`confidence_map`:** when halo is all `low`/`medium` from patterns, note that in `culture_preferences` / `interests` reasons.
6. **User-task nudge:** “Infer culture from employer/org patterns and interests from elective subjects; use medium/low; leave `[]` when no pattern.”

---

## Product honesty

You cannot recover rich interests from a keyword-only resume. You *can* often recover **thin culture** from employer types and constraint language. The win is systematic **tiered inference + empty-when-honest**, not forcing both arrays to be non-empty.
