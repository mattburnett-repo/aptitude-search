"""Prune older agent step observations to limit context growth."""

from __future__ import annotations

from smolagents.memory import ActionStep

from app.config import config


def _first_line(text: str, *, max_len: int = 120) -> str:
    line = text.strip().splitlines()[0] if text.strip() else ""
    if len(line) > max_len:
        return line[: max_len - 3].rstrip() + "..."
    return line


def prune_agent_memory(memory_step: ActionStep, agent) -> None:
    """
    After each action step, replace observations on older steps with short summaries.

    Registered as a smolagents step_callback; does not modify smolagents itself.
    """
    keep_recent = config.llm.job_discovery_memory_keep_recent_steps
    pruned_max = config.llm.job_discovery_memory_pruned_observation_max_chars
    current = memory_step.step_number

    for step in agent.memory.steps:
        if not isinstance(step, ActionStep):
            continue
        steps_ago = current - step.step_number
        if steps_ago < keep_recent:
            continue

        if step.observations:
            summary = _first_line(step.observations)
            step.observations = f"[Step {step.step_number}] {summary}"

        if step.model_output:
            output = str(step.model_output)
            if len(output) > pruned_max:
                half = pruned_max // 2
                step.model_output = (
                    output[:half] + "\n...[pruned]...\n" + output[-half:]
                )
