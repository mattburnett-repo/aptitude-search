# Faster reload (local build → dump → restore)

Alternative to streaming INSERTs Mac → Render: build on local Postgres, ship once.

**Connection (`data/onet-conninfo.sh`)** — this script does not store credentials. It prints whatever is in **`backend/config.toml` → `[onet]`** (host, port, database, user, password, sslmode). You edit `[onet]` before each phase, then run the same command:

| Phase                     | Edit `[onet]` to point at                                                                   | Typical `sslmode` |
| ------------------------- | ------------------------------------------------------------------------------------------- | ----------------- |
| Local hydrate + `pg_dump` | **Local** Postgres (e.g. `host = "localhost"`, your local `database` / `user` / `password`) | `disable`         |
| `pg_restore`              | **Render** Postgres (Render dashboard external URL fields)                                  | `require`         |

Same script, two different `[onet]` blocks in config — switch `[onet]`, then run `./data/onet-conninfo.sh` to confirm host and database before long jobs.

1. **Hydrate locally** — set `[onet]` to local, then run `./data/load-onet-postgres.sh`.
2. **`pg_dump`** — still with `[onet]` on **local**; save to a meaningful filename:

```bash
pg_dump -Fc -f onet_30_3_full.dump -d "$(./data/onet-conninfo.sh)"
```

(`-Fc` = custom format, required for `pg_restore`.)

3. **`pg_restore`** — set `[onet]` to **Render**, then:

```bash
pg_restore --no-owner --no-acl -d "$(./data/onet-conninfo.sh)" onet_30_3_full.dump
```

The dump file **stays on your Mac**. Nothing gets uploaded to a Render file folder. `pg_restore` reads the file locally and writes into Render over the Postgres connection.

On Render (pgAdmin or `psql`): `CREATE EXTENSION IF NOT EXISTS vector;` before restore if the dump includes `occupation_embeddings`, or before running the embed script.

`pg_dump` and `pg_restore` are local programs (same client bundle as `psql`).
