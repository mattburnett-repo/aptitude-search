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
#   ONET_EMBED_ONLY=1 ./data/load-onet-postgres.sh   # load embed-required tables only (~24% of INSERTs)
#   ONET_RESET_SCHEMA=0 ./data/load-onet-postgres.sh   # append without wipe
#   ONET_VERBOSE=1 ./data/load-onet-postgres.sh        # show every INSERT line
#   ONET_LOG_FILE=data/onet-load.log ./data/load-onet-postgres.sh
#
# Connection: backend/config.toml [onet] (via data/onet-conninfo.sh)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_DIR="${ONET_SQL_DIR:-${SCRIPT_DIR}/download/db_30_3_mysql}"
PYTHON="${REPO_ROOT}/backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
ONET_CONNINFO="$("${SCRIPT_DIR}/onet-conninfo.sh")"
ONET_CONNINFO_LABEL="$("${PYTHON}" -c "
import sys
sys.path.insert(0, '${REPO_ROOT}/backend')
from app.core.config import config
print(f'{config.onet.host}:{config.onet.port}/{config.onet.database}')
")"
LOG_FILE="${ONET_LOG_FILE:-}"
RESET_SCHEMA="${ONET_RESET_SCHEMA:-1}"
EMBED_ONLY="${ONET_EMBED_ONLY:-0}"
PSQL_QUIET=(-q)

# FK-safe subset for occupation_profile_from_onet.sql (see data/docs/onet-embedding-required-tables.md).
EMBED_ONLY_SQL_FILES=(
  01_content_model_reference.sql
  03_occupation_data.sql
  04_scales_reference.sql
  12_abilities.sql
  24_essential_skills.sql
  25_transferable_skills.sql
  28_work_activities.sql
  36_job_titles.sql
)

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

echo "postgres: $ONET_CONNINFO_LABEL"
echo "sql dir:  $SQL_DIR"
if [[ "$EMBED_ONLY" == "1" ]]; then
  echo "mode:     embed-only (${#EMBED_ONLY_SQL_FILES[@]} files)"
else
  echo "files:    $SQL_COUNT"
fi
echo "reset:    $RESET_SCHEMA"
echo


if [[ "$RESET_SCHEMA" == "1" ]]; then
  echo "wiping public schema..."
  psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$ONET_CONNINFO" \
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
    patch_sql_for_postgres "$file" | psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$ONET_CONNINFO" >>"$LOG_FILE" 2>&1
  else
    patch_sql_for_postgres "$file" | psql "${PSQL_QUIET[@]}" -v ON_ERROR_STOP=1 -d "$ONET_CONNINFO"
  fi
}

load_sql_files() {
  if [[ "$EMBED_ONLY" == "1" ]]; then
    local name
    for name in "${EMBED_ONLY_SQL_FILES[@]}"; do
      local file="${SQL_DIR}/${name}"
      if [[ ! -f "$file" ]]; then
        echo "error: embed-only file not found: $file" >&2
        exit 1
      fi
      echo "==> ${name}"
      run_psql "$file"
    done
    return
  fi

  while IFS= read -r file; do
    echo "==> $(basename "$file")"
    run_psql "$file"
  done < <(find "$SQL_DIR" -maxdepth 1 -name '[0-9]*.sql' | sort -V)
}

load_sql_files

echo
if [[ "${ONET_SKIP_EMBED:-}" != "1" ]]; then
  echo "==> build_occupation_embeddings.py"
  "$PYTHON" "${SCRIPT_DIR}/embed/build_occupation_embeddings.py"
else
  "${SCRIPT_DIR}/embed/create-occupation-embeddings-table.sh"
  echo "embed step skipped (ONET_SKIP_EMBED=1)"
fi

echo
echo "done. verify with:"
echo "  python data/smoke_onet_postgres.py"
echo "  ONET_CONNINFO=\$(./data/onet-conninfo.sh)"
echo "  psql -d \"\$ONET_CONNINFO\" -c \"SELECT COUNT(*) FROM occupation_data;\""
echo "  psql -d \"\$ONET_CONNINFO\" -c \"SELECT COUNT(*) FROM occupation_embeddings;\""
