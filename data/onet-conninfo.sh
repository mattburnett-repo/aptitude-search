#!/usr/bin/env bash
# Print libpq conninfo from backend/config.toml [onet] for psql and shell scripts.
#
# Usage: ONET_CONNINFO="$("${SCRIPT_DIR}/onet-conninfo.sh")"

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

print(config.onet.conninfo())
'
