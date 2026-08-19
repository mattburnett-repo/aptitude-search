# What is an aptitude? (premise)

First-principles product premise — not how Stage 1 / the schema currently behave. Culture/interest *extraction* rules live in sibling v0.8.4 notes; the **0.8.3 ship** of those fields is in [`docs/v0.8.3/culture-preferences-and-backend-cleanup.md`](../v0.8.3/culture-preferences-and-backend-cleanup.md).

---

## Premise (2026-08-13)

**Question:** What exactly is an “aptitude”? Revisit the project premise; do not treat current app fields as the definition.

**Answer:** Aptitude is **a capacity to do a kind of thing well** — often before/beyond specific tools and titles. If the word is just a bag of skills, titles, and preferences, it is branding. The product has a distinct premise only if aptitude is **the thing that transfers when the keywords change**.

### Not aptitude

| Concept | Answers | Example |
|--------|---------|---------|
| Skill | What can they do with a tool/method? | Python, Salesforce |
| Knowledge | What do they know? | Logistics, HIPAA |
| Experience | What have they done? | 8 years, two migrations |
| Strength | What performance pattern shows up? | Ownership under ambiguity |
| Preference | What do they want? | Remote, mission-driven |
| Personality | How do they tend to behave? | Conscientious |
| Interest | What draws them? | Climate, ops |
| Fit | Match to a specific env/role | This startup, this posting |

### Three coherent meanings (pick one)

1. **Psychometric capacity** — stable-ish abilities (verbal, numerical, spatial, etc.). Resume is a weak source; needs tests.
2. **Demonstrated work capacity** — kinds of *work* they repeatedly succeed at, independent of stack (e.g. “bring order to messy systems”). Inferred from history.
3. **Occupational potential** — plausible role families they could grow into. A *prediction from* aptitude, not aptitude itself.

Culture preferences are none of the three; they constrain *where* capacity is applied.

### Product definition

> An aptitude is a transferable capacity for a kind of work, evidenced by repeated success patterns — not the tools used to do it, and not what the person says they want.

Then: name those capacities (and confidence). Skills, domains, titles, culture, remote, salary sit around it as evidence or filters.

Alternative: psychometric (1) — but then a resume-only pipeline is the wrong instrument.

**Decision:** extract aptitudes **and** still capture nearby signals as supporting context — labeled as supporting signals, not as aptitude.

---

## Standing product rules

- **Personality:** out. Not useful or reliable from a resume. Do not invent Big Five from bullets. Behavioral *work* patterns ≠ personality (`working_style_signals` / `strengths` instead).
- **Fit:** not a Stage 1 field. Fit is ranking against a posting/environment (Stage 3).
- **Constraints:** location, remote, salary, industries include/exclude stay on `constraints` — not duplicated into the profile.
- **Supporting signals still in scope** on a good-faith, omit-over-invent basis (skill, knowledge, experience, strength; preference/interest only when evidenced). Resume-friendliness varies.

### Resume-only capture (signals other than culture/interest)

| Signal | Resume-only? | Notes |
|--------|----------------|-------|
| Skill | Yes | Resumes are built for this. |
| Knowledge | Partial | Domain/industry often present; depth vs name-drop is the risk. |
| Experience | Yes (facts) | Titles, tenure, employers, seniority. |
| Strength | Yes (infer) | Repeated patterns; keep evidence + confidence. |
| Personality | No | See standing rules above. |
| Fit | No (as extract) | Computed later against a posting. |

Culture preferences and interests: inference tiers, proxies, and thin-resume honesty are in [`culture-interests-thin-resume-inference.md`](culture-interests-thin-resume-inference.md). Stage 1 prompt reframing (core + halo) is in [`stage1-prompt-revision-plan.md`](stage1-prompt-revision-plan.md).
