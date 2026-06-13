#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE="${ENV_FILE:-.env}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

PORT="${PORT:-3001}"

if pids=$(lsof -ti:"$PORT" 2>/dev/null); then
  echo "Port $PORT in use (PIDs: $pids); stopping..."
  kill $pids 2>/dev/null || true
  sleep 0.5
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment at .venv..."
  python3 -m venv .venv
fi

VENV_DIR="$(pwd)/.venv"
export VIRTUAL_ENV="$VENV_DIR"
PATH="$VENV_DIR/bin:$PATH"
export PATH

exec "$VENV_DIR/bin/python" -m uvicorn app.main:app --reload --port "$PORT"
