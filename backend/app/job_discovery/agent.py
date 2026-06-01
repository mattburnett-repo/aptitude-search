"""Stage 2 job discovery via smolagents (web search + page visits)."""

from smolagents import (
    AgentError,
    AgentGenerationError,
    AgentMaxStepsError,
    InferenceClientModel,
    ToolCallingAgent,
)
from smolagents.monitoring import LogLevel

from app.config import config
from app.job_discovery.tool_observed_urls import ToolObservedUrlRegistry
from app.job_discovery.tools import build_job_discovery_tools


def _runtime_with_cause(summary: str, exc: BaseException) -> RuntimeError:
    cause = exc.__cause__
    detail = f"{summary}\nCause: {cause}" if cause is not None else summary
    return RuntimeError(detail)


def run_job_discovery_agent(
    system_prompt: str,
    user_message: str,
    model_id: str | None = None,
    *,
    max_steps: int = 10,
    observed_urls: ToolObservedUrlRegistry | None = None,
) -> str:
    """Run the job-discovery agent; returns final text (expected: JSON fenced block)."""
    resolved_model = model_id or config.llm.job_discovery_model
    hf_model = InferenceClientModel(
        model_id=resolved_model,
        token=config.llm.job_discovery_model_key,
    )
    url_registry = observed_urls if observed_urls is not None else ToolObservedUrlRegistry()
    agent = ToolCallingAgent(
        tools=build_job_discovery_tools(url_registry),
        model=hf_model,
        instructions=system_prompt,
        max_steps=max_steps,
        # Agent console trace (steps, tool calls, page text): set to LogLevel.INFO or LogLevel.DEBUG.
        verbosity_level=LogLevel.OFF,
        name="job_discovery_agent",
        description=(
            "Searches the web for job openings. Run multiple searches and visits; "
            "return many distinct postings with direct URLs in final JSON."
        ),
    )
    try:
        output = agent.run(user_message)
    except AgentGenerationError as exc:
        raise _runtime_with_cause(
            "Job discovery agent failed while calling the model "
            "(often after a failed search or very long context). "
            "Retry with a shorter resume or fewer constraints.",
            exc,
        ) from exc
    except AgentMaxStepsError as exc:
        raise _runtime_with_cause(
            f"Job discovery agent exceeded max_steps ({max_steps}) before returning JSON.",
            exc,
        ) from exc
    except AgentError as exc:
        raise _runtime_with_cause(f"Job discovery agent error: {exc}", exc) from exc
    if isinstance(output, str):
        return output.strip()
    if hasattr(output, "output") and output.output is not None:
        return str(output.output).strip()
    return str(output).strip()
