#!/usr/bin/env python3
"""Smoke-test Stage 2 job discovery agent (web search). Run from backend/: .venv/bin/python scripts/smoke_job_discovery_agent.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import config
from app.job_discovery import run_job_discovery_agent


def main() -> None:
    print(f"job_discovery_model: {config.llm.job_discovery_model}")
    print(f"job_discovery_model_key: {'set' if config.llm.job_discovery_model_key else 'missing'}")
    print(f"max_steps: {config.llm.job_discovery_max_steps}")
    text = run_job_discovery_agent(
        system_prompt="You are a job search assistant. Use web search, then reply briefly with what you found.",
        user_message="Search for one remote software engineer job posting in Toronto and summarize the title and URL.",
        max_steps=3,
    )
    print("--- agent output (truncated) ---")
    print(text[:2000])


if __name__ == "__main__":
    main()
