#!/usr/bin/env bash
# Ensure occupation_embeddings table exists and is empty.
#
# Requires O*NET occupation_data already loaded (data/load-onet-postgres.sh).
# Database name: backend/config.toml [onet].database (via data/onet-database.sh)
#
# Usage:
#   ./data/ingest/create-occupation-embeddings-table.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PGDATABASE="$("${DATA_DIR}/onet-database.sh")"
SQL_FILE="${SCRIPT_DIR}/occupation_embeddings.sql"

if [[ ! -f "$SQL_FILE" ]]; then
  echo "error: SQL file not found: $SQL_FILE" >&2
  exit 1
fi

echo "database: $PGDATABASE"
echo "occupation_embeddings: ensuring table (see ${SQL_FILE})..."
psql -q -v ON_ERROR_STOP=1 -d "$PGDATABASE" -f "$SQL_FILE"
echo "occupation_embeddings: ready (empty)"
