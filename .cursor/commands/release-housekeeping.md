# Release housekeeping

Run the standard **aptitude-search** release housekeeping workflow for a versioned ship.

## Version (required)

If the user did **not** provide a version in this message, **stop and ask**:

> What release version? (e.g. `0.6.2` — use semver `x.y.z`, no leading `v` in the answer)

Normalize input:

- Accept `0.6.2`, `v0.6.2`, or `V0.6.2` → use **`0.6.2`** for paths, changelog, and `package.json`; use **`v0.6.2`** for the git tag.

## Scope

Use **current branch changes** (and this conversation if relevant) as the source of truth for what shipped. Do not invent features.

Plans for this project are authoritative **only** under **`.cursor/plans/`** (see `.cursor/rules/plan-authority.mdc`).

## Documentation

1. Create **`docs/v{VERSION}/`** (e.g. `docs/v0.6.2/`).
2. Add one markdown file with a **short, descriptive slug** (e.g. `lighthouse-and-security-polish.md`) containing:
   - What changed and why
   - User-facing behavior (if any)
   - Backend / frontend / tests / docs sections as applicable
   - Explicit “unchanged” notes where relevant
   - Link to **`docs/changelog/{VERSION}.md`**
   - Footer: `[{VERSION}]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v{VERSION}`

3. Create **`docs/changelog/{VERSION}.md`** following existing entries (e.g. `docs/changelog/0.6.1.md`):
   - Title: `# {VERSION} — YYYY-MM-DD` (today’s date)
   - One-line summary; note **Frontend is `{VERSION}`** when the web app changed
   - Sections: Frontend, Backend, Tests, Documentation (write “No changes.” when empty)
   - Same GitHub release footer link
   - Trailing `---`

## Version bump

- If this release includes **frontend** changes, set **`frontend/package.json`** `"version"` to **`{VERSION}`**.
- Do not bump unrelated packages unless the user explicitly asks.

## Pre-commit checks

When frontend changed:

```bash
cd frontend && npm test && npm run build
```

Fix failures before commit.

When backend changed, run relevant backend tests if feasible before commit.

## Git

Commit is **requested** by invoking this command. Follow the user’s git safety rules:

1. In parallel: `git status`, `git diff`, `git log -3 --oneline`
2. Stage all release-related files. **Do not** stage secrets (`.env`, `.env.local`, `backend/config.toml`, credentials).
3. Commit with a HEREDOC message, e.g.:

   ```text
   Release v{VERSION}: {one-line summary of why}.
   ```

4. Create tag **`v{VERSION}`**
5. Push: `git push origin HEAD && git push origin v{VERSION}`  
   Request network/git permissions; use smart-mode approval if main is protected.
6. Confirm commit hash, tag name, and clean working tree.

## Do not

- Create or cite plans outside **`.cursor/plans/`**
- Force-push, amend prior release commits, or skip hooks unless the user explicitly asks
- Add unrelated refactors or “while we’re here” cleanups
