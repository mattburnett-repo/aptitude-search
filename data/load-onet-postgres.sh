#!/usr/bin/env bash
# Load O*NET 30.3 MySQL-format SQL dumps into PostgreSQL (01..45, FK-safe order).
#
# Wipes public schema by default, then loads all tables. Patches files 31–32 for
# Postgres (O*NET FKs reference no UNIQUE constraint in the upstream dump).
# On success, creates occupation_embeddings (empty) and runs build_occupation_embeddings.py.
#
# Usage:
#   ./data/load-onet-postgres.sh
#   ONET_SKIP_EMBED=1 ./data/load-onet-postgres.sh   # load O*NET only, skip Hugging Face embed
#   ONET_RESET_SCHEMA=0 ./data/load-onet-postgres.sh   # append without wipe
#   ONET_VERBOSE=1 ./data/load-onet-postgres.sh        # show every INSERT line
#   ONET_LOG_FILE=data/onet-load.log ./data/load-onet-postgres.sh
#
# Database name: backend/config.toml [onet].database (via data/onet-database.sh)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_DIR="${ONET_SQL_DIR:-${SCRIPT_DIR}/download/db_30_3_mysql}"
PGDATABASE="$("${SCRIPT_DIR}/onet-database.sh")"
PYTHON="${REPO_ROOT}/backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
LOG_FILE="${ONET_LOG_FILE:-}"
RESET_SCHEMA="${ONET_RESET_SCHEMA:-1}"
PSQL_QUIET=(-q)

if [[ "${ONET_VERBOSE:-}" == "1" ]]; then
  PSQL_QUIET=()
fi

if [[ ! -d "$SQL_DIR" ]]; then
  echo "error: SQL directory not found: $SQL_DIR" >&2
  exit 1
fi

SQL_COUNT=0
for _ in "$SQL_DIR"/[0-9]*.sql; do
  [[ -e "$_" ]] || continue
  SQL_COUNT=$((SQL_COUNT + 1))
done
if [[ "$SQL_COUNT" -eq 0 ]]; then
  echo "error: no numbered .sql files in $SQL_DIR" >&2
  exit 1
fi

echo "database: $PGDATABASE"
echo "sql dir:  $SQL_DIR"
echo "files:    $SQL_COUNT"
echo "reset:    $RESET_SCHEMA"
echo


if [[ "$RESET_SCHEMA" == "1" ]]; then
  echo "wiping public schema..."
  psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$PGDATABASE" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo
fi

# O*NET 31/32 reference element_name without a UNIQUE/PK on that column; Postgres rejects it.
# Upstream .sql files use CRLF; strip \r before sed so line anchors match.
patch_sql_for_postgres() {
  local file=$1
  local base
  base="$(basename "$file")"
  case "$base" in
    31_gwas_to_iwas.sql)
      tr -d '\r' <"$file" | sed \
        -e '/FOREIGN KEY (iwa_element_name) REFERENCES content_model_reference(element_name)/d' \
        -e 's/FOREIGN KEY (iwa_element_id) REFERENCES content_model_reference(element_id),$/FOREIGN KEY (iwa_element_id) REFERENCES content_model_reference(element_id));/'
      ;;
    32_gwas_to_iwas_to_dwas.sql)
      tr -d '\r' <"$file" | sed \
        -e '/FOREIGN KEY (dwa_element_name) REFERENCES content_model_reference(element_name)/d' \
        -e 's/FOREIGN KEY (dwa_element_id) REFERENCES content_model_reference(element_id),$/FOREIGN KEY (dwa_element_id) REFERENCES content_model_reference(element_id));/'
      ;;
    *)
      cat "$file"
      ;;
  esac
}

run_psql() {
  local file=$1
  local base
  base="$(basename "$file")"
  if [[ "$base" == "31_gwas_to_iwas.sql" || "$base" == "32_gwas_to_iwas_to_dwas.sql" ]]; then
    echo "    (postgres FK patch applied)"
  fi
  if [[ -n "$LOG_FILE" ]]; then
    patch_sql_for_postgres "$file" | psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$PGDATABASE" >>"$LOG_FILE" 2>&1
  else
    patch_sql_for_postgres "$file" | psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$PGDATABASE"
  fi
}

while IFS= read -r file; do
  echo "==> $(basename "$file")"
  run_psql "$file"
done < <(find "$SQL_DIR" -maxdepth 1 -name '[0-9]*.sql' | sort -V)

echo
"${SCRIPT_DIR}/ingest/create-occupation-embeddings-table.sh"

if [[ "${ONET_SKIP_EMBED:-}" != "1" ]]; then
  echo
  echo "==> build_occupation_embeddings.py"
  "$PYTHON" "${SCRIPT_DIR}/ingest/build_occupation_embeddings.py"
else
  echo
  echo "embed step skipped (ONET_SKIP_EMBED=1)"
fi

echo
echo "done. verify with:"
echo "  python data/smoke_onet_postgres.py"
echo "  psql -d $PGDATABASE -c \"SELECT COUNT(*) FROM occupation_data;\""
echo "  psql -d $PGDATABASE -c \"SELECT COUNT(*) FROM occupation_embeddings;\""
