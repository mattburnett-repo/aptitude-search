"""Integration smoke test for O*NET Postgres load (data/smoke_onet_postgres.py).

Skipped by default. Run against a database already loaded via data/load-onet-postgres.sh:

  cd backend
  ONET_SMOKE_TEST=1 pytest tests/test_onet_smoke.py -v

Requires backend/config.toml with a working [onet] section (not config.test.toml).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
SMOKE_SCRIPT = REPO_ROOT / "data" / "smoke_onet_postgres.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("smoke_onet_postgres", SMOKE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SMOKE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["smoke_onet_postgres"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.integration
def test_onet_postgres_smoke() -> None:
    if os.environ.get("ONET_SMOKE_TEST") != "1":
        pytest.skip("Set ONET_SMOKE_TEST=1 to run against a loaded O*NET database")

    config_path = BACKEND_DIR / "config.toml"
    if not config_path.is_file():
        pytest.skip("backend/config.toml required for O*NET smoke test")

    import app.core.config as config_module

    config_module.config = config_module.Config.load(config_path)

    smoke = _load_smoke_module()
    exit_code = smoke.run_checks()
    assert exit_code == 0
