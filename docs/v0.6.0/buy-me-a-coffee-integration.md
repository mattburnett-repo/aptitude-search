# Buy Me a Coffee integration (v0.6.0)

> **Superseded in v0.6.1.** The footer button is now a static styled link (`BuyMeACoffeeButton.tsx`); the BMC script embed described below was removed. See **[docs/v0.6.1/lighthouse-and-security-polish.md](../v0.6.1/lighthouse-and-security-polish.md)** for the current implementation.

Design and implementation notes for optional support links on the Aptitude Search frontend. No pipeline or API changes.

## Goals

- Integrate [Buy Me a Coffee](https://buymeacoffee.com/aptitude.search) without hard-selling or obtrusive marketing.
- Keep support passive: text links and a single footer button, no floating widget, no post-run modal.

## Support URL

Configured via environment variable (not hardcoded in source):

```env
VITE_SUPPORT_URL=https://buymeacoffee.com/aptitude.search
```

Committed defaults live in:

- `frontend/.env.development`
- `frontend/.env.production`

When `VITE_SUPPORT_URL` is unset, support copy renders as plain text with no links or button.

## UI touchpoints

| Location | Behavior |
|----------|----------|
| **Input trust notes** | “Donations” links to the BMC page (input screen only). |
| **Site footer** | BMC button embed, centered below the tagline. |
| **Jobs step (stage 5)** | Quiet footnote after job cards: “Helpful? Donations are always appreciated.” — only when `results.length > 0`. |

The Jobs footnote sits **outside** `.verified-matches` so it is excluded from **Save as PDF** export.

## Footer button embed

BMC provides a script embed with `data-*` attributes. That script uses `document.writeln()` on load, which only works during initial HTML parsing — **not** when injected by React after mount.

**Fix:** load `button.prod.min.js` once into `<head>`, then call `window.bmcBtnWidget(...)` and assign the returned HTML to the footer container (`frontend/src/lib/buyMeACoffee.ts`).

Button styling (slug, colors, Cookie font, “Buy me a coffee” label) matches the BMC dashboard embed. Footer CSS scales the default widget down (~70% of stock size) with slightly larger text (20px) for readability.

## Shared components

- `frontend/src/config/support.ts` — reads `VITE_SUPPORT_URL`.
- `frontend/src/components/SupportLink.tsx` — muted accent link used in trust notes and Jobs footnote.
- `frontend/src/lib/buyMeACoffee.ts` — script loader + `bmcBtnWidget` renderer for the footer.

## Explicitly not included

- BMC floating corner widget
- Branded popup or modal after pipeline completion
- Second BMC button on the Jobs step (footnote uses text link only; footer keeps the button)
- Support UI when job search returns zero results

## Tests

- `frontend/tests/components/SiteChrome.test.tsx` — trust note + footer button wiring.
- `frontend/tests/lib/buyMeACoffee.test.ts` — `bmcBtnWidget` render path.
- `frontend/tests/components/VerifiedMatchesDisplay.test.tsx` — Jobs footnote shown/hidden by result count.

## Related changelog

- **`docs/changelog/0.6.0.md`**

[0.6.0]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.6.0
