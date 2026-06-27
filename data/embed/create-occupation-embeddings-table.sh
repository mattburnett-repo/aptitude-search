#!/usr/bin/env bash
# Ensure occupation_embeddings table exists and is empty.
#
# Requires O*NET occupation_data already loaded (data/load-onet-postgres.sh).
# vector(N) uses [embedding].dimensions from backend/config.toml.
# Connection: backend/config.toml [onet] (via data/onet-conninfo.sh)
#
# Usage:
#   ./data/embed/create-occupation-embeddings-table.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${DATA_DIR}/.." && pwd)"
BACKEND="${REPO_ROOT}/backend"
PYTHON="${BACKEND}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi

echo "occupation_embeddings: ensuring table ([embedding].dimensions from config)..."
BACKEND_DIR="${BACKEND}" DATA_DIR="${DATA_DIR}" exec "$PYTHON" -c '
import os
import subprocess
import sys

sys.path.insert(0, os.environ["BACKEND_DIR"])
from app.core.config import config

dimensions = config.embedding.dimensions
conninfo = config.onet.conninfo()
sql = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS occupation_embeddings (
  onetsoc_code       character(10) PRIMARY KEY
                     REFERENCES occupation_data (onetsoc_code),
  occupation_profile text NOT NULL,
  embedding          vector({dimensions}) NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS occupation_embeddings_embedding_hnsw_idx
  ON occupation_embeddings
  USING hnsw (embedding vector_cosine_ops);

TRUNCATE occupation_embeddings;
"""
result = subprocess.run(
    ["psql", "-q", "-v", "ON_ERROR_STOP=1", "-d", conninfo],
    input=sql,
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode != 0:
    detail = (result.stderr or result.stdout or "psql failed").strip()
    print(f"error: {detail}", file=sys.stderr)
    sys.exit(result.returncode)
print(f"occupation_embeddings: ready (empty, vector({dimensions}))")
'
