#!/usr/bin/env bash
# Print [onet].database from config.toml so shell scripts use the same DB name as Python.
#
# Usage: PGDATABASE="$(data/onet-database.sh)"

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
_BACKEND="${_REPO_ROOT}/backend"
_PYTHON="${_BACKEND}/.venv/bin/python"
if [[ ! -x "$_PYTHON" ]]; then
  _PYTHON=python3
fi

BACKEND_DIR="${_BACKEND}" exec "$_PYTHON" -c '
import os
import sys

sys.path.insert(0, os.environ["BACKEND_DIR"])
from app.core.config import config

print(config.onet.database)
'
