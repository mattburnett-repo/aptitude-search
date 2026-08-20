# A11y scan (frontend)

Scan **aptitude-search** frontend UI for accessibility deficiencies using the installed a11y MCP servers. Summarize findings, propose concise fixes, then **stop and wait for explicit user approval** before changing any files.

## Scope

| Default | Path / target |
|---------|----------------|
| Source | `frontend/src/**/*.{tsx,jsx,css}` (components, `App.tsx`, `main.tsx`, `index.css`) |
| Tests | Skip `frontend/tests/**` unless the user asks |
| Live page | Always audit. Default URL: `http://localhost:5173`. Use a user-provided URL when given (e.g. preview/prod). |

If the user names specific files, routes, or components, limit the **code** scan to those. Still run the live page audit unless they explicitly skip it (e.g. “code only”).

## Tools (required)

Discover schemas with `GetMcpTools` before calling if needed. Authenticate with `mcp_auth` only if a server returns auth errors.

**a11y-expert** (`project-0-aptitude-search-a11y-expert`):

1. `review_code` — primary code scan. Pass each relevant component’s source (JSX/TSX). Set `component_type` when clear (e.g. form, button, dialog, landmarks).
2. `check_contrast` — for theme/text pairs from `frontend/src/index.css` (light and dark `[data-theme]` tokens such as text/bg, muted/bg, CTA text/bg, secondary button text/bg). Report AA failures.
3. `get_pattern` / `list_patterns` — only when a finding needs a concrete WAI-ARIA pattern (modal, tabs, combobox, etc.). Do not dump patterns for every file.

**a11y** (`project-0-aptitude-search-a11y`) — **required** each run:

1. Resolve URL: user-provided if any, else `http://localhost:5173`.
2. `get_summary` first for the URL.
3. `audit_webpage` with `includeHtml: true` and tags `wcag2aa`, `wcag21aa`, `best-practice` when summary shows issues or when more detail is needed to map findings to source.
4. If the URL is unreachable or the audit fails, say so in **Out of scope / skipped**, remind that local audit needs `cd frontend && npm run dev`, and continue with code review + contrast — do not block the whole command.

## Workflow

1. **Inventory** — List UI files in scope (glob `frontend/src/**/*.{tsx,jsx}` plus `index.css`).
2. **Code review** — Call `review_code` on each in-scope component (batch MCP calls where practical). Deduplicate repeated issues (e.g. same pattern across displays).
3. **Contrast** — Spot-check critical CSS variable pairs in light and dark themes via `check_contrast`.
4. **Live audit** — Always run `get_summary` (and `audit_webpage` as above) on the resolved URL. Merge with code findings; prefer unique issues; tag items as runtime-only vs source-only when useful.
5. **Report** — Present one concise summary (format below). **Do not edit files.**
6. **Gate** — End with an explicit approval question. Implement **only** after the user clearly approves (e.g. “yes”, “apply all”, “fix 1 and 3”). If they approve a subset, implement only that subset.
7. **Implement (after approval only)** — Smallest fixes that address approved items. Match existing patterns. Do not expand into unrelated refactors or design restyles.
8. **Re-check** — After implementing, briefly re-run `review_code` on touched files and re-run the live audit on the same URL; confirm remaining issues.

## Report format

Keep the chat reply tight:

1. **Verdict** — one line (e.g. “N issues across M files” or “No material a11y issues found”). Include the live audit URL.
2. **Findings** — numbered list. Each item:
   - **Where** — file path and/or live DOM selector (and element/role if known)
   - **Issue** — short deficiency
   - **Fix** — one concise suggested change (not a full rewrite)
   - **Severity** — critical / serious / moderate / minor (best effort from MCP output)
3. **Out of scope / skipped** — only if relevant (unreachable live URL, tests skipped, “code only”, etc.).
4. **Approval prompt** — e.g. “Approve applying all fixes, a subset (by number), or none?”

Do not paste large MCP dumps or full component rewrites in the summary.

## Do not

- Change any code, CSS, or config **before** explicit user approval
- Treat silence or “looks good” about the report as approval to implement
- Scan backend, fixtures, or docs unless asked
- Invent WCAG failures the MCP tools did not support
- Rewrite visual design or add new UI patterns beyond what approved fixes require
- Create plans outside `.cursor/plans/` or unrelated documentation
