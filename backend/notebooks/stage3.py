"""LangGraph Stage 3 with search-engine fan-out / fan-in.

Leaves ``app.pipeline.run_stage3`` and the rest of ``app/`` unchanged.
Search uses spike-local ``search.py`` (one DDGS engine per worker), not
``app.job_discovery.tools``.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnusedCallResult=false
# ruff: noqa: E402  — path bootstrap below must run before app/search imports

from __future__ import annotations

import logging
import operator
import sys
from pathlib import Path
from typing import Annotated, NotRequired, TypedDict

# Notebook/cwd may be notebooks/; ensure backend/ and this spike dir are importable.
_SPIKE_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _SPIKE_DIR.parent
for _path in (_BACKEND_ROOT, _SPIKE_DIR):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from langgraph.graph import END, START, StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.types import Send

from app.core.json_types import FoundJob, JsonObject, as_object_dict
from app.core.models import Constraints
from app.core.progress import ProgressCallback, emit_progress
from app.core.validate import validate_stage
from app.job_discovery import (
    build_discovery_queries,
    empty_job_discovery_results,
    rank_and_filter_found_jobs,
    synthesize_job_discovery_results,
)
from search import search_queries_on_backend  # pyright: ignore[reportImplicitRelativeImport]
from tool_observed_urls import (  # pyright: ignore[reportImplicitRelativeImport]
    ToolObservedUrlRegistry,
    filter_results_to_tool_observed_urls,
)

# Spike-local DDGS engines only (production Stage 3 uses Tavily; not in config).
_SPIKE_SEARCH_BACKENDS = ("brave", "yahoo", "yandex")

logger = logging.getLogger(__name__)

DEFAULT_CONSTRAINTS = Constraints()


class Stage3State(TypedDict):
    aptitude_profile: JsonObject
    constraints: Constraints
    role_family_plan: NotRequired[JsonObject | None]
    queries: NotRequired[list[str]]
    # Fan-out workers append; reduce reads these then writes found_jobs.
    partial_jobs: Annotated[list[FoundJob], operator.add]
    observed_urls: Annotated[list[str], operator.add]
    found_jobs: NotRequired[list[FoundJob]]
    verified_matches: NotRequired[JsonObject]


class Stage3StateUpdate(TypedDict, total=False):
    queries: list[str]
    partial_jobs: list[FoundJob]
    observed_urls: list[str]
    found_jobs: list[FoundJob]
    verified_matches: JsonObject


class SearchWorkerState(TypedDict):
    queries: list[str]
    backend: str


def _dedupe_jobs_by_url(jobs: list[FoundJob]) -> list[FoundJob]:
    found: list[FoundJob] = []
    seen: set[str] = set()
    for job in jobs:
        url = str(job.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        found.append(job)
    return found


def _registry_from_urls(urls: list[str]) -> ToolObservedUrlRegistry:
    registry = ToolObservedUrlRegistry()
    for url in urls:
        registry.record_url(url)
    return registry


def plan_queries(
    state: Stage3State,
    *,
    on_progress: ProgressCallback | None = None,
) -> Stage3StateUpdate:
    emit_progress(
        "Stage 3: Searching the web for job postings…",
        on_progress=on_progress,
    )
    queries = build_discovery_queries(
        state["aptitude_profile"],
        state["constraints"],
        role_family_plan=state.get("role_family_plan"),
    )
    if not queries:
        logger.warning("stage3 graph built zero queries from profile")
    return {"queries": queries}


def route_engines(state: Stage3State) -> list[Send] | str:
    """One parallel worker per configured search engine (not a serial loop)."""
    queries = state.get("queries") or []
    backends = list(_SPIKE_SEARCH_BACKENDS)
    if not queries or not backends:
        return "reduce_filter_fit"
    return [
        Send("run_engine_search", {"queries": queries, "backend": backend})
        for backend in backends
    ]


def run_engine_search(state: SearchWorkerState) -> Stage3StateUpdate:
    backend = state["backend"]
    queries = state["queries"]
    jobs, observed = search_queries_on_backend(queries, backend=backend)
    logger.info(
        "stage3 run_engine_search backend=%r queries=%s jobs=%s",
        backend,
        len(queries),
        len(jobs),
    )
    return {
        "partial_jobs": jobs,
        "observed_urls": observed,
    }


def reduce_filter_fit(
    state: Stage3State,
    *,
    on_progress: ProgressCallback | None = None,
) -> Stage3StateUpdate:
    # Spike: do not run production filter_found_jobs (it drops list/search URLs
    # that notebooks/search.py intentionally keeps and scrapes).
    found_jobs = _dedupe_jobs_by_url(list(state.get("partial_jobs") or []))
    if found_jobs:
        emit_progress("Ranking by aptitude work-pattern fit…", on_progress=on_progress)
        ranked = rank_and_filter_found_jobs(
            found_jobs,
            state["aptitude_profile"],
            role_family_plan=state.get("role_family_plan"),
        )
        removed = len(found_jobs) - len(ranked)
        if removed:
            logger.info("stage3 aptitude_fit removed %s low-fit row(s)", removed)
        found_jobs = ranked
    return {"found_jobs": found_jobs}


def synthesize(
    state: Stage3State,
    *,
    on_progress: ProgressCallback | None = None,
) -> Stage3StateUpdate:
    profile = state["aptitude_profile"]
    constraints = state["constraints"]
    role_family_plan = state.get("role_family_plan")
    found_jobs = list(state.get("found_jobs") or [])
    registry = _registry_from_urls(list(state.get("observed_urls") or []))

    if found_jobs:
        emit_progress(
            f"Found {len(found_jobs)} job posting(s). Preparing verified job listings…",
            on_progress=on_progress,
        )
        result = synthesize_job_discovery_results(
            profile,
            constraints,
            found_jobs,
            role_family_plan=role_family_plan,
        )
        result = filter_results_to_tool_observed_urls(result, registry)
    else:
        emit_progress(
            "No job postings found; preparing empty results…",
            on_progress=on_progress,
        )
        result = empty_job_discovery_results(
            profile,
            constraints,
            role_family_plan=role_family_plan,
        )

    emit_progress("Validating results…", on_progress=on_progress)
    validate_stage("jobDiscovery", result)
    emit_progress("Stage 3 complete.", on_progress=on_progress)
    return {"verified_matches": result}


def build_stage3_graph(
    *,
    on_progress: ProgressCallback | None = None,
) -> CompiledStateGraph[Stage3State, None, Stage3State, Stage3State]:
    """Compile Stage 3 map/reduce graph. Progress closes over ``on_progress``."""

    def _plan(state: Stage3State) -> Stage3StateUpdate:
        return plan_queries(state, on_progress=on_progress)

    def _reduce(state: Stage3State) -> Stage3StateUpdate:
        return reduce_filter_fit(state, on_progress=on_progress)

    def _synthesize(state: Stage3State) -> Stage3StateUpdate:
        return synthesize(state, on_progress=on_progress)

    builder = StateGraph(Stage3State)
    builder.add_node("plan_queries", _plan)
    builder.add_node("run_engine_search", run_engine_search, input_schema=SearchWorkerState)
    builder.add_node("reduce_filter_fit", _reduce, defer=True)
    builder.add_node("synthesize", _synthesize)

    builder.add_edge(START, "plan_queries")
    builder.add_conditional_edges(
        "plan_queries",
        route_engines,
        ["run_engine_search", "reduce_filter_fit"],
    )
    builder.add_edge("run_engine_search", "reduce_filter_fit")
    builder.add_edge("reduce_filter_fit", "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()


def run_stage3(
    aptitude_profile: JsonObject,
    constraints: Constraints | None = None,
    *,
    role_family_plan: JsonObject | None = None,
    on_progress: ProgressCallback | None = None,
    max_concurrency: int | None = None,
) -> JsonObject:
    """Same call shape as ``app.pipeline.run_stage3``; fan-out per search engine."""
    c = constraints or DEFAULT_CONSTRAINTS
    validate_stage("constraints", c.model_dump())

    backends = list(_SPIKE_SEARCH_BACKENDS)
    concurrency = max_concurrency if max_concurrency is not None else max(len(backends), 1)

    graph = build_stage3_graph(on_progress=on_progress)
    final = graph.invoke(
        {
            "aptitude_profile": aptitude_profile,
            "constraints": c,
            "role_family_plan": role_family_plan,
            "partial_jobs": [],
            "observed_urls": [],
        },
        config={"max_concurrency": concurrency},
    )
    verified = as_object_dict(final.get("verified_matches"))
    if verified is None:
        raise RuntimeError("Stage 3 graph finished without verified_matches")
    return verified
