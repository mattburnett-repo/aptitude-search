#!/usr/bin/env python3
"""Validate golden fixture JSON against stage schemas."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import config
from app.core.paths import FIXTURES_DIR
from app.core.validate import validate_stage


def main() -> int:
    failed = 0
    for entry in config.fixtures.files:
        name, stage = entry.name, entry.stage
        data = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
        try:
            validate_stage(stage, data)
            print(f"OK  {name}")
        except ValueError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
