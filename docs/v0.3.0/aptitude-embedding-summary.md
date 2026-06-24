## Emerging System Direction: Aptitude Profiles + Semantic Role Matching

The core direction of the project is shifting from keyword-based job search toward semantic matching between a candidate's demonstrated aptitude and the kinds of work represented by different roles.

Traditional job search often works like this:

```text
resume keywords -> job keywords
```

The intended direction is closer to:

```text
candidate aptitude profile -> role families / work modes -> targeted job discovery
```

References to embeddings or vector search are useful as analogies for this idea, but they are not the current implementation target. The design goal is comparability: representing both candidates and roles in a way that can be compared, explained, and refined.

## Current Role of Prompt 1

Prompt 1 functions as a structured aptitude representation layer. It compresses resume data into semantic signals such as:

- technical and domain capabilities
- work patterns
- adjacent role possibilities
- adaptability signals
- evidence of how the person solves problems

This is not a true mathematical embedding system. It is better understood as ontology discovery: identifying which aptitude signals are meaningful enough to drive later matching decisions.

The project is currently in:

- ontology discovery
- signal design
- semantic modeling exploration

It is not yet:

- production ML architecture
- vector infrastructure
- a finalized matching engine

## Role Semantics

The complementary problem is determining the semantics of roles. Instead of asking only whether a posting contains a keyword, the system should ask what kind of work the role actually represents.

Useful sources for role semantics include:

1. **Job posting text**  
   Responsibilities, required skills, seniority, domain, tools, outcomes, and collaboration patterns are the lowest-friction source.

2. **Structured job metadata**  
   Schema.org `JobPosting` fields, ATS fields, department labels, requisition categories, location, employment type, compensation, and level can all provide useful context.

3. **Occupation taxonomies**  
   O*NET, ESCO, and SOC/BLS categories can help normalize role types, skills, work activities, and occupational families beyond the wording of a single company.

4. **Company and product context**  
   The same title can mean different things depending on whether the company is SaaS, healthcare, fintech, logistics, AI tooling, ecommerce, devtools, a marketplace, an agency, or another kind of organization.

5. **Career-site structure and title signals**  
   URL paths, department pages, team pages, category filters, and title modifiers can reveal role semantics. Examples include `/engineering/platform`, `/product/data`, `Senior`, `Staff`, `Implementation`, `Solutions`, `Growth`, or `Research`.

6. **Responsibility versus requirement separation**  
   "What you'll do" often reveals the role better than "what you need." Requirement lists are frequently inflated or generic.

7. **LLM extraction into a role profile**  
   A prompt can convert postings into a structured role capability profile, especially when paired with schema validation and a small manual review set.

The most useful near-term combination is likely job text, structured metadata, LLM extraction, and optional occupation-taxonomy normalization.

## Intermediate Role-Family Matching

A practical intermediate step is to identify likely role families before searching for specific jobs. Instead of searching the whole job market directly, the system first asks:

```text
What kinds of work does this person appear suited for?
```

The output is not limited to software engineering. It should be broad enough to surface occupational families and work modes such as:

```text
Software / Engineering
Data / Analytics
Product / Strategy
Operations / Process
Customer Success / Solutions
Technical Writing / Documentation
Research / Analysis
Training / Enablement
Implementation / Professional Services
Security / Compliance
Marketing / Growth
Business Systems / RevOps
```

This gives job discovery a smaller and more justified search space. It also creates an explanation layer:

```text
This candidate appears aligned with Operations / Process Improvement because...
This candidate may also fit Technical Writing / Documentation because...
Avoid quota-carrying sales roles because...
```

An intermediate artifact could look like:

```json
{
  "recommended_role_families": [
    {
      "role_family": "Operations / Process Improvement",
      "fit_reason": "...",
      "supporting_signals": ["systems thinking", "cross-functional coordination"],
      "work_modes": ["process design", "stakeholder coordination", "workflow optimization"],
      "search_terms": ["operations analyst", "process improvement specialist"],
      "avoid_terms": ["sales quota", "cold calling"]
    }
  ]
}
```

This step may be more useful in the near term than trying to compare every job directly against the profile. First infer plausible kinds of work, then search within those role families.

## Validation Question

The key validation question is whether Prompt 1 outputs can be used to identify role families and role-specific search terms that produce better job discovery results than keyword search alone.

Success should be judged by whether the system can:

- surface relevant roles the candidate may not have known to search for
- reduce obvious false positives
- explain why a role family is or is not a fit
- preserve transferable and adjacent capabilities
- remain broad across occupational categories, not just software roles

The current prompt system is valuable as an exploratory semantic compression layer. Its purpose is to discover the meaningful aptitude and role signals before deciding what kind of matching system, if any, should be built around them.