# Sentry backend error monitoring (v0.7.0)

Optional production error reporting for the FastAPI API on Render. Alerts when real failures occur during use (unhandled exceptions, streaming pipeline crashes). No frontend or pipeline behavior changes.

## Problem

Deploy-failure notifications from Vercel/Render do not cover runtime application errors after a successful deploy. The primary user path (`POST /v1/pipeline?stream=1`) catches exceptions and returns NDJSON error events, so middleware alone would miss most production failures.

## Solution

### 1. Optional Sentry SDK init

When `SENTRY_DSN` is set (e.g. on Render):

- `sentry_sdk.init()` in `backend/app/main.py` before the FastAPI app is created
- `environment` from `SENTRY_ENVIRONMENT` (use `production` on Render, `development` locally)
- `traces_sample_rate=0.0` — errors only, no performance tracing
- `send_default_pii=False` — do not attach resume/request PII to error reports

When `SENTRY_DSN` is unset, Sentry is disabled (local dev and CI unchanged).

### 2. Error capture paths

| Path | Mechanism |
|------|-----------|
| Unhandled exceptions (500 handler) | `sentry_sdk.capture_exception` in `unhandled_exception_handler` |
| Streaming pipeline (`?stream=1`) | `sentry_sdk.capture_exception` in `stream_pipeline.py` `except Exception` |
| FastAPI middleware | Enabled automatically via `sentry-sdk[fastapi]` |

Intentional `HTTPException` responses (400, 422) are not reported.

### 3. Render setup

Environment variables on the backend web service:

| Variable | Example |
|----------|---------|
| `SENTRY_DSN` | DSN from Sentry project settings |
| `SENTRY_ENVIRONMENT` | `production` |

Configure a Sentry alert rule: **“A new issue is created”** → email (or Slack).

Local optional test: add the same vars to `backend/.env` (not committed); verify once, then remove any debug routes.

## User-facing behavior

- No changes. Users see the same error responses as before.
- Operators receive Sentry emails when new backend issues appear.

## Unchanged

- Frontend (Vercel) — no Sentry integration in this release
- Pipeline stages, schemas, prompts
- `config.toml` — DSN is env-only, not in TOML config

## Related changelog

- **`docs/changelog/0.7.0.md`**

[0.7.0]: https://github.com/mattburnett-repo/aptitude-search/releases/tag/v0.7.0
