# Get logs (Render + Sentry + Vercel)

Summarize production logs and error signals for **aptitude-search** from Render, Sentry, and Vercel.

## Time range

- If the user specifies a window (e.g. `6h`, `7d`, `since yesterday`), use that.
- If **not** specified, default to the **past 24 hours**.
- Convert relative windows to absolute RFC3339 `startTime` / `endTime` (UTC) for Render metrics/logs.
- Use Sentry `period` when it maps cleanly (`24h`, `7d`, `14d`, `30d`); otherwise use an equivalent absolute window in the query text.
- For Vercel, prefer relative `since` values the tools accept (`24h`, `7d`, etc.). Pair `since`/`until` for Web Analytics when aggregating over a fixed window.

## Scope

| System | Target |
|--------|--------|
| Render | Web service **`aptitude-search-api`** (`srv-d91bmvbtqb8s739hku8g`) in workspace **My Workspace** (`tea-cspubnhu0jms73844500`) |
| Sentry | Org **`self-ngh`** (`regionUrl`: `https://us.sentry.io`), project **`aptititude-search`** |
| Vercel | Frontend project for **https://aptitude-search.vercel.app/** (slug typically **`aptitude-search`**). Resolve `projectId` / `teamId` from `frontend/.vercel/project.json` if present, else `list_projects` / `list_teams`. |

Do **not** summarize unrelated Render services (chat-mvp, servepoint, suspended apps) or unrelated Vercel projects unless the user asks.

## Tools

Use MCP (discover schemas with `GetMcpTools` before calling if needed):

**Render** (`project-0-aptitude-search-render`):

1. Pass `workspaceId` on every call (or `list_workspaces` + confirm if unset). Prefer explicit `workspaceId` over session `select_workspace` when there is a single known workspace.
2. Confirm service with `list_services` if the service id is unknown or changed.
3. `list_logs` — app logs for the window (`resource: [serviceId]`, `direction: backward`). Also query `level: [error, warning, critical]` and `statusCode: [4*, 5*]` when useful.
4. `list_log_label_values` — discover `statusCode`, `path`, `level` present in the window.
5. `get_metrics` — at least `cpu_usage`, `memory_usage`, `http_request_count` (aggregate by `statusCode` when possible); include `http_latency` / `bandwidth_usage` if helpful. Use a resolution that fits the window (e.g. hourly for 24h).
6. `list_deploys` — note any deploys that fall inside the window; otherwise record the live deploy and when it went live.

**Sentry** (`project-0-aptitude-search-sentry`):

1. `find_organizations` / `find_projects` only if org/project slugs are unknown.
2. `search_events` — error **count** (`dataset: errors`, aggregate `count()`), top titles if any, plus **logs** (`dataset: logs`) and **spans** (`dataset: spans`) for the same period.
3. `search_issues` — issues with activity in the window (e.g. `lastSeen:-24h` or period=`24h`), and unresolved issues for the project.
4. Do **not** widen beyond the requested window unless the user asks.

**Vercel** (`project-0-aptitude-search-vercel`):

1. Resolve `projectId` and `teamId` (see Scope). Cache them for the rest of the run.
2. `get_runtime_errors` — grouped runtime error clusters for the window (`since` like `24h` / `7d`). **Max lookback is 7 days**; if the user asks for longer, note the cap and use 7d for this tool.
3. `get_runtime_logs` — production runtime output for the window. Prefer `environment: production`; also query `level: [error, warning, fatal]` and/or `statusCode: "5xx"` / `"4xx"` when useful. For wide windows, use `group_by` (`level`, `statusCode`, `requestPath`) for counts instead of paging every line.
4. `get_web_analytics` — traffic for the same window:
   - `mode: count` for totals (visitors / pageviews)
   - `mode: aggregate` with `since`/`until` and `by: ["day"]` (or `hour` for ≤24h) for time series
   - Optionally aggregate by `requestPath`, `country`, `deviceType`, or `browserName` when it adds signal
5. `list_deployments` — note production deploys in the window; pull `get_deployment_build_logs` only if a deploy failed.
6. Do **not** call deploy/buy/protection-update tools as part of this command.

## Workflow

1. Resolve the time range (default **24h**).
2. Fetch Render, Sentry, and Vercel data in parallel where possible.
3. If Render or Vercel returns **no logs** for the window, say so explicitly; optionally note the **most recent prior** log/deploy timestamp for context (do not treat prior activity as in-window).
4. Summarize what matters: errors, 4xx/5xx, deploys, traffic vs idle, CPU/memory anomalies, Sentry issues/events, Vercel runtime errors and web analytics.
5. Present results as a **canvas** under the workspace `canvases/` directory (e.g. `render-sentry-vercel-24h.canvas.tsx`), following the canvas skill: embed data inline, charts for time series when present, skip empty placeholder sections. Link the canvas in the chat reply.
6. Keep the chat reply short: verdict first, then a few bullets for Render, Sentry, and Vercel.

## Output expectations

- Lead with a clear verdict (quiet / issues found).
- Call out **zero** traffic or **zero** errors when that is the finding — quiet is a valid result.
- Include service URL / dashboard links only when useful.
- Do not change code, configs, resolve Sentry issues, or mutate Vercel project settings unless the user asks.

## Do not

- Default to any window other than **24 hours** when the user omits a timeframe
- Summarize the whole Render or Vercel account by default
- Invent log lines or error counts
- Expand to 90d (or similar) Sentry history unless requested
- Pretend Vercel runtime-error history beyond **7 days** is available
