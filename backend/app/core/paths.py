"""Repo-root Path constants for dirs named in ``[paths]`` (``config.toml``).

``config.paths`` holds relative strings only. This module resolves them once
against ``REPO_ROOT`` so callers use ``Path`` objects (``PROMPTS_DIR / name``)
instead of repeating ``__file__`` walks or hard-coded directory literals.

The app still expects those dirs on disk; this centralizes the layout, it does
not virtualize it.
"""

from pathlib import Path

from app.core.config import config

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = REPO_ROOT / config.paths.prompts_dir
SCHEMAS_DIR = REPO_ROOT / config.paths.schemas_dir
FIXTURES_DIR = REPO_ROOT / config.paths.fixtures_example_outputs_dir
