# Marketing copy refresh (v0.6.2)

Start-page and SEO copy updated to emphasize **non-obvious job search paths** — the product differentiator beyond title/keyword search. No pipeline or API changes.

## Rationale

After v0.6.0/v0.6.1 (BMC support and Lighthouse/security), messaging still described a generic “resume → careers → jobs” flow. New copy leads with paths users would not find through obvious searches, aligned with aptitude-driven role families and Stage 3 discovery.

## User-facing changes

| Location | Before | After |
|----------|--------|-------|
| **Hero eyebrow** | Career intelligence | Beyond the obvious job searches |
| **Hero lead** | Upload your resume… in one pipeline | Discover non-obvious job search paths… all in one go |
| **Footer tagline** | resume-driven career matching and job discovery | beyond the obvious job search |
| **Meta description** | Upload your resume to infer aptitudes… | Same theme as hero lead (SEO/snippet alignment) |

**Unchanged:** H1 (“Find work that fits your real strengths”), input steps, trust notes, BMC support UI, pipeline behavior.

## Tooling

- **`.cursor/commands/commit-tag-push.md`** — project slash command for versioned release docs, bump, commit, tag, and push.

## Backend

- No changes.

## Tests

- No test updates required (copy-only; existing frontend tests unchanged).

## Related

- **`docs/changelog/0.6.2.md`**

[0.6.2]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.6.2
