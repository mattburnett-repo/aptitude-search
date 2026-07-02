# Lighthouse and security polish (v0.6.1)

Follow-up to v0.6.0 Buy Me a Coffee integration. A Lighthouse audit of the production deployment flagged **Best Practices at 77%**, driven mainly by third-party cookies from the BMC widget script and missing security headers. This release addresses those issues without changing pipeline or API behavior.

## Problem (Lighthouse, pre-0.6.1)

| Category | Score (Vercel) | Main finding |
|----------|----------------|--------------|
| Best Practices | 77 | Six third-party cookies from `cdnjs.buymeacoffee.com` on every page load |
| Best Practices | 77 | No Content-Security-Policy in enforcement mode |
| SEO | 90 | Missing `<meta name="description">` |

The BMC **button embed script** (`button.prod.min.js`) loaded on mount and set session cookies even when users never clicked support. That is expected for their widget but conflicts with a privacy-respectful, Lighthouse-friendly frontend.

Performance and Accessibility on production were already strong (99+). Local `npm run dev` scores are not comparable to minified Vercel builds.

## Solution

### 1. Static footer button (replace BMC script)

Removed `frontend/src/lib/buyMeACoffee.ts` and all runtime loading of `cdnjs.buymeacoffee.com`.

Added **`BuyMeACoffeeButton.tsx`**: a plain `<a>` to `VITE_SUPPORT_URL` styled to match the v0.6.0 widget:

- Background `#40DCA5`, white Cookie font, “Buy me a coffee” label
- Inline SVG cup icon (yellow `#FFDD00`, black outline)
- Same compact footer dimensions as the scaled v0.6.0 button

Visual appearance is preserved; only the implementation changes (no third-party JS or cookies on page load). Clicking still opens the BMC page in a new tab.

Config colors and label live in **`frontend/src/lib/bmcButtonConfig.ts`**.

### 2. Security headers on Vercel

Added **`frontend/vercel.json`** response headers for all routes:

- **Content-Security-Policy** — `script-src 'self'` (no BMC CDN); fonts/styles allow Google Fonts; `connect-src` allows HTTPS/WSS for API calls
- **Cross-Origin-Opener-Policy** — `same-origin`
- **X-Frame-Options** — `DENY`
- **X-Content-Type-Options** — `nosniff`
- **Referrer-Policy** — `strict-origin-when-cross-origin`
- **Permissions-Policy** — disables camera, microphone, geolocation

Headers apply on **Vercel deploy only**, not the Vite dev server.

### 3. CSP-compatible theme bootstrap

Inline theme script in `index.html` moved to **`frontend/public/theme-init.js`** so CSP does not require `'unsafe-inline'` for scripts.

### 4. SEO meta description

Added a concise `<meta name="description">` in `index.html`.

## Unchanged from v0.6.0

- Input trust note “donations” link (`SupportLink.tsx`)
- Jobs-step footnote when results exist (`VerifiedMatchesDisplay.tsx`)
- `VITE_SUPPORT_URL` / `frontend/src/config/support.ts`
- No backend or pipeline changes

## Files touched

| Add | Remove / replace |
|-----|------------------|
| `BuyMeACoffeeButton.tsx` | `buyMeACoffee.ts` |
| `bmcButtonConfig.ts` | `buyMeACoffee.test.ts` |
| `vercel.json` | `window.bmcBtnWidget` types in `vite-env.d.ts` |
| `public/theme-init.js` | Dynamic script injection in `SiteChrome.tsx` |
| `BuyMeACoffeeButton.test.tsx` | |

## Tests

- `SiteChrome.test.tsx` — static BMC link in footer
- `BuyMeACoffeeButton.test.tsx` — link href, styling class, empty when URL unset

## Expected Lighthouse impact (production, post-deploy)

- **Best Practices:** third-party cookie audit cleared; CSP present via Vercel
- **SEO:** meta description audit passed
- **Performance:** unchanged vs v0.6.0 production build (slightly less third-party work)

Re-run Lighthouse on **https://aptitude-search.vercel.app** after deploy—not `localhost:5173` dev—for authoritative scores.

## Related

- **`docs/v0.6.0/buy-me-a-coffee-integration.md`** — original BMC UX design (footer script approach superseded here)
- **`docs/changelog/0.6.1.md`**

[0.6.1]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.6.1
