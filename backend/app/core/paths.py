from pathlib import Path

from app.core.config import config

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = REPO_ROOT / config.paths.prompts_dir
SCHEMAS_DIR = REPO_ROOT / config.paths.schemas_dir
FIXTURES_DIR = REPO_ROOT / config.paths.fixtures_example_outputs_dir
