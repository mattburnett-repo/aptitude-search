# O\*NET data pipeline

Load O\*NET 30.3 into Postgres, build occupation embeddings, and verify the result.

## Prerequisites

1. **Postgres** with client tools (`psql`, optional `pg_dump` / `pg_restore`)
2. **pgvector** extension available on the server (`CREATE EXTENSION vector`)
3. **`backend/config.toml`** — copy from `backend/config.example.toml` and set:
   - `[onet]` — Postgres host, database, user, password, `sslmode`
   - `[embedding]` — Hugging Face `model_key`, `model`, `dimensions`, `provider` (must support `feature-extraction`)
4. **Python venv** — `pip install -r backend/requirements.txt` (use `backend/.venv`)
5. **O\*NET SQL dumps** — not committed; see [download/README.md](download/README.md)

`occupation_embeddings.embedding` uses `vector(N)` where `N` is `[embedding].dimensions`. If you change `dimensions` in config, drop the table before re-running embed (`DROP TABLE occupation_embeddings CASCADE;`).

Confirm connection before long jobs:

```bash
./data/onet-conninfo.sh
```

## Quick start

From repo root:

```bash
./data/load-onet-postgres.sh
python data/smoke_onet_postgres.py
```

## Layout

| Path | Purpose |
|------|---------|
| `download/` | O\*NET 30.3 MySQL-format SQL (local only; gitignored) |
| `embed/` | `occupation_embeddings` table + profile SQL + HF embed build |
| `docs/` | Runbooks and INSERT-count reference |
| `load-onet-postgres.sh` | Load O\*NET (full or embed-only), then embed |
| `onet-conninfo.sh` | Print libpq conninfo from `[onet]` |
| `smoke_onet_postgres.py` | Post-load verification (also via pytest; see below) |

## `load-onet-postgres.sh` environment

| Variable | Default | Effect |
|----------|---------|--------|
| `ONET_SKIP_EMBED` | unset | Set to `1` to load O\*NET only (creates empty `occupation_embeddings`, skips HF) |
| `ONET_EMBED_ONLY` | unset | Set to `1` to load only the 8 tables required for embed (~24% of INSERTs) |
| `ONET_RESET_SCHEMA` | `1` | Set to `0` to append without `DROP SCHEMA public CASCADE` |
| `ONET_VERBOSE` | unset | Set to `1` to show every INSERT line |
| `ONET_LOG_FILE` | unset | e.g. `data/onet-load.log` — append psql output to file |
| `ONET_SQL_DIR` | `data/download/db_30_3_mysql` | Override SQL source directory |
| `ONET_EMBED_BATCH_SIZE` | `16` | HF batch size for `build_occupation_embeddings.py` |

Pipeline runtime (`backend/config.toml`):

| Setting | Section | Effect |
|---------|---------|--------|
| `enabled` | `[onet_matching]` | required in `config.toml`; set `false` to skip O\*NET vector search in Stage 2 |
| `top_k` | `[onet_matching]` | Max O\*NET occupations passed to Stage 2 LLM |
| `min_similarity` | `[onet_matching]` | Drop matches below this cosine similarity (0–1) |

Examples:

```bash
ONET_SKIP_EMBED=1 ./data/load-onet-postgres.sh
ONET_EMBED_ONLY=1 ./data/load-onet-postgres.sh
ONET_VERBOSE=1 ONET_LOG_FILE=data/onet-load.log ./data/load-onet-postgres.sh
backend/.venv/bin/python data/embed/build_occupation_embeddings.py
```

## Smoke test (CLI or pytest)

```bash
python data/smoke_onet_postgres.py
# or, against a loaded DB with backend/config.toml [onet] configured:
cd backend && ONET_SMOKE_TEST=1 pytest tests/test_onet_smoke.py -v
```

## Further reading

- [docs/onet-faster-reload.md](docs/onet-faster-reload.md) — local build → `pg_dump` → Render restore
- [docs/onet-embedding-required-tables.md](docs/onet-embedding-required-tables.md) — tables used by embed SQL
- [docs/db_30_3_mysql-insert-counts.md](docs/db_30_3_mysql-insert-counts.md) — INSERT counts per file

## License

O\*NET database files are [CC BY 4.0](https://www.onetcenter.org/license_db.html). See root [README.md](../README.md#third-party-data).
