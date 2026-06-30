# Frontend styling & UX polish

> **Status (v0.4.1):** Done. Appearance-only pass on the v0.4.0 wizard. No pipeline or API behavior changes. PDF export blocks remain light/high-contrast.

## Goal

The app worked but looked bland. Improve visual personality and engagement without changing functionality. Success metric: the app simply looks better.

## Design references

Initial inspiration from three career-tool sites:

| Site | Traits borrowed |
|------|-----------------|
| [Retuner AI](https://www.retunerai.com/) | Product polish, card panels, clear primary CTA |
| [JobJokk](https://www.jobjokk.com/) | Human tone, generous spacing, section cards |
| [WorqAI](https://www.worqai.io/en) | **Chosen color direction** — dark-first, high contrast, green “optimization” accent, numbered steps, terminal-style progress |

## Visual system (WorqAI-biased)

### Tokens

CSS custom properties in `frontend/src/index.css` under `[data-theme="light"]` and `[data-theme="dark"]`:

| Token | Dark | Light |
|-------|------|-------|
| Background | `#09090b` | `#fafafa` |
| Surface | `#141416` | `#ffffff` |
| Primary CTA | white fill / dark text | dark fill / light text |
| Accent | `#4ade80` | `#15803d` |
| Borders | `#27272a` | `#d4d4d8` |

Replaced the prior Google-blue primary (`#4a7cff`) with dark/white CTAs and green accents.

### Typography

- **Inter** — UI font (Google Fonts, `index.html`)
- **JetBrains Mono** — pipeline progress log only (`--font-mono`)

### Default theme

New visitors default to **dark** when no `localStorage.theme` is set (`index.html` boot script + `useTheme.ts`).

## UI changes by area

### Page shell

- Tagline under title: *“Discover roles that fit your real strengths.”*
- Header border separation; light mode gets a subtle header gradient
- `#root` max-width `880px`

### Input screen

- Bullet subtitle replaced with **01 / 02 / 03** step strip
- Resume + Go wrapped in `.input-panel` card
- Primary button: **Go →** (full-width on narrow viewports)

### Running screen

- **Stage label** parsed from progress messages, e.g. `Stage 2 of 3 — Matching aptitude to O*NET occupations…`
- Spinner while loading
- Progress log: JetBrains Mono, `>` prefix on active line, `✓` on completed lines
- Prefix markers kept inside the panel (no left overflow/clipping from collapsible `overflow: hidden`)

### Step indicator nav

Horizontal pill bar shown on `running` + `stage1`–`stage5`:

| # | Label | View |
|---|-------|------|
| 01 | Profile | `stage1` |
| 02 | Confidence | `stage2` |
| 03 | Matches | `stage3` |
| 04 | Roles | `stage4` |
| 05 | Jobs | `stage5` |

Behaviors:

- **Clickable** once pipeline `result` exists; navigates via `setView`
- **Disabled** while pipeline is running (no result) or during PDF export (`stepNavDisabled`)
- **Active step** highlighted: green border, tinted background, accent number
- Step 01 **pulses** during running before results arrive
- Completed steps (visited earlier in the flow) show green step numbers
- No text-selection flash on click: `user-select: none`, `outline` only on `:focus-visible`

### Result panels

- Collapsibles and cards: flat surfaces, `1px` borders (WorqAI style, not heavy shadows)
- Light mode: subtle box-shadow on input panel, collapsibles, running label
- Aptitude summary: green left accent bar
- Job cards: hover border accent; **high-confidence** postings get green left border (`.job-card-high-confidence`)
- Role-family entries styled as individual cards
- Occupation matches as bordered card rows

### Buttons

| Class | Role |
|-------|------|
| `.primary-cta` | Go, Next → |
| `.secondary` | Outlined actions |
| `.back` | Amber Back |
| `.secondary.success` | Green Start over |

## Scope guard (intentionally not done)

- No CSS framework (Tailwind, etc.)
- No drag-and-drop upload
- No marketing landing page
- PDF export override blocks untouched (`.aptitude-profile--pdf-export`, etc.)

## Files touched

| File | Changes |
|------|---------|
| `frontend/index.html` | Fonts, default dark theme |
| `frontend/src/index.css` | Tokens, components, step indicator, progress log, cards |
| `frontend/src/App.tsx` | Step indicator, input steps, running label, layout wrappers |
| `frontend/src/components/PipelineActions.tsx` | Go → label |
| `frontend/src/components/VerifiedMatchesDisplay.tsx` | High-confidence job card class |
| `frontend/src/hooks/useTheme.ts` | Default dark when unset |
| `frontend/tests/App.test.tsx` | Go → button name |
| `frontend/tests/components/PipelineActions.test.tsx` | Go → button name |

## Implementation phases (as shipped)

1. Tokens, font, palette swap (WorqAI)
2. Page shell, header, tagline
3. Input panel + numbered steps
4. Step indicator (later made clickable)
5. Cards, collapsibles, buttons
6. Running UX: spinner, stage label, terminal log, checkmarks
7. Default dark theme + light mode polish
8. Follow-up fixes: progress log overflow, active-step highlight, nav click selection flash, “Plan” → “Roles” label
