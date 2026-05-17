# Changelog

## [1.0.3] - 2026-05-17

### Changed

- Documentation aligned to the implemented **two-stage** workflow (aptitude profile → verified job discovery)
- Stage 2 documented as single JSON fenced block (`job-discovery-results.schema.json`), not separate SEARCH PLAN / NOTES markdown sections

## [1.0.2] - 2026-05-17

### Changed

- Renamed `web/` folder to `frontend/`

## [1.0.1] - 2026-05-17

### Changed

- Replaced Node/Hono API with Python/FastAPI under `backend/` (folder formerly `api/`)

## [1.0.0] - 2026-05-17

### Added

- Two-prompt workflow: resume → aptitude profile; profile → verified job discovery
- JSON schemas: aptitude profile, job discovery results, constraints
- Sample resumes and stage-1 golden example output
- Buyer workflow guide (`docs/WORKFLOW.md`)
- Orchestration API and MVP web app (BYO API key)
