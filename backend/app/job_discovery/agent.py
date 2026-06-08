"""Stage 2 job discovery via smolagents (web search + page visits)."""

import json
import logging
from typing import Any

from langsmith import traceable
from smolagents import (
    AgentError,
    AgentGenerationError,
    AgentMaxStepsError,
    CodeAgent,
    InferenceClientModel,
)
from smolagents.monitoring import LogLevel

from app.core import prompt_loader
from app.core.config import config
from app.job_discovery.memory_prune import prune_agent_memory
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.tools import build_job_discovery_tools

logger = logging.getLogger(__name__)


def _runtime_with_cause(summary: str, exc: BaseException) -> RuntimeError:
    cause = exc.__cause__
    detail = f"{summary}\nCause: {cause}" if cause is not None else summary
    return RuntimeError(detail)


def _normalize_found_jobs(raw: Any) -> list[dict[str, Any]]:
    """Coerce agent final_answer / state into a list of job dicts."""
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            jobs = parsed.get("found_jobs") or parsed.get("results")
            if isinstance(jobs, list):
                return [item for item in jobs if isinstance(item, dict)]
    return []


def _resolve_found_jobs(
    agent_state: dict[str, Any],
    run_output: Any,
) -> list[dict[str, Any]]:
    jobs = _normalize_found_jobs(agent_state.get("found_jobs"))
    if jobs:
        return jobs
    return _normalize_found_jobs(run_output)


@traceable(run_type="chain", name="job_discovery_agent")
def run_job_discovery_agent(
    system_prompt: str,
    user_message: str,
    *,
    max_steps: int | None = None,
    observed_urls: ToolObservedUrlRegistry | None = None,
) -> list[dict[str, Any]]:
    """Run discovery agent; returns found_jobs list for synthesis phase."""
    if max_steps is None:
        max_steps = config.llm.job_discovery_max_steps
    job_discovery_model = InferenceClientModel(
        model_id=config.llm.job_discovery_model,
        token=config.llm.job_discovery_model_key,
    )
    url_registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    agent = CodeAgent(
        tools=build_job_discovery_tools(url_registry),
        model=job_discovery_model,
        prompt_templates=prompt_loader.code_agent_prompt_templates(),
        instructions=system_prompt,
        max_steps=max_steps,
        max_print_outputs_length=config.llm.job_discovery_max_print_outputs_length,
        additional_authorized_imports=["json"],
        step_callbacks=[prune_agent_memory],
        verbosity_level=LogLevel.OFF,
        name="job_discovery_agent",
        description="Searches the web for job openings and returns found_jobs.",
    )
    agent_state: dict[str, Any] = {"found_jobs": [], "visited_urls": []}
    try:
        run_result = agent.run(
            user_message,
            return_full_result=True,
            additional_args=agent_state,
        )
    except AgentGenerationError as exc:
        raise _runtime_with_cause(
            "Job discovery agent failed while calling the model "
            "(often after a failed search or too much tool context). "
            "Retry with fewer constraints.",
            exc,
        ) from exc
    except AgentMaxStepsError as exc:
        raise _runtime_with_cause(
            f"Job discovery agent exceeded max_steps ({max_steps}) before returning found_jobs.",
            exc,
        ) from exc
    except AgentError as exc:
        raise _runtime_with_cause(f"Job discovery agent error: {exc}", exc) from exc

    if run_result.token_usage is not None:
        logger.info(
            "job_discovery_agent token_usage input=%s output=%s steps=%s",
            run_result.token_usage.input_tokens,
            run_result.token_usage.output_tokens,
            len(run_result.steps),
        )
    for step in run_result.steps:
        observations = step.get("observations")
        if observations:
            logger.info(
                "job_discovery_agent step=%s observation_chars=%s",
                step.get("step_number"),
                len(observations),
            )

    found_jobs = _resolve_found_jobs(agent_state, run_result.output)
    logger.info("job_discovery_agent found_jobs count=%s", len(found_jobs))
    return found_jobs
