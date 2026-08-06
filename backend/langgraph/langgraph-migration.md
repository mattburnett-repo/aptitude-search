# LangGraph migration (backend)

Start with the stage pipeline as a **linear LangGraph**, keep stage internals as plain Python, and avoid turning this into an agent framework rewrite on day one.

## What you have today

`run_pipeline` is already a straight chain:

```
prepare_resume → stage1 → stage2 → stage3 → result
```

Stage 3 is itself a small sub-chain (discovery → filter → aptitude fit → synthesize/empty). LLM calls are Hugging Face chat completions (`complete_chat_json`), not LangChain. `smolagents` is mostly a Tool base + `VisitWebpageTool` for scraping—not agent orchestration.

So LangGraph’s job here is **orchestration + shared state**, not replacing discovery/search/validation.

## Simplest mental model

LangGraph needs three ideas:

1. **State** — one `TypedDict` passed through every step
2. **Nodes** — functions `(state) -> partial state update`
3. **Edges** — which node runs next (`START → … → END`)

For this product, that maps cleanly:

```text
START
  → prepare_resume
  → stage1_aptitude
  → stage2_role_family
  → stage3_discovery
  → stage3_fit          # filter + rank (can stay one node)
  → stage3_synthesize
  → END
```

Keep Stage 3 as **one node** at first if that feels less overwhelming; split discovery/fit/synthesize later only if it helps clarity or testing.

## Recommended shape (clarity over cleverness)

**State** (mirror what the API already returns, plus inputs):

```python
class PipelineState(TypedDict, total=False):
    resume: str
    constraints: dict  # or Constraints
    aptitude_profile: dict
    role_family_plan: dict
    occupation_matches: list
    found_jobs: list
    verified_matches: dict
```

**Nodes** = thin wrappers around existing functions:

- `run_stage1`, `run_stage2`, `run_stage3` stay as the real logic
- Graph nodes only read/write state and call those functions

**Do not** (for v1):

- Rewrite HF calls into LangChain chat models
- Build a ReAct / tool-calling agent for Stage 3 (discovery is already deterministic Python)
- Add checkpointers, human-in-the-loop, parallel branches, or subgraphs
- Invent new abstractions “because LangGraph has them”

A linear graph that does what `run_pipeline` does today is the right first win.

## Migration order (low overwhelm)

1. **Spike**: one file, one graph, three nodes wrapping existing stage functions; `graph.invoke({...})` returns the same shape as `PipelineResult`.
2. **Swap** `run_pipeline` to call the compiled graph; keep `/v1/stages/{1,2,3}` calling the same underlying functions.
3. **Progress**: keep `on_progress` via config/closure at invoke time, or emit from nodes—don’t redesign streaming yet.
4. **Only then** consider Stage 3 as an inner graph, and whether `smolagents` can go away (plain functions + a small scrape helper).

## Where to trim over-coding (while converting)

| Area | Why it’s a candidate |
|------|----------------------|
| `smolagents.Tool` around `search_job_postings` | Discovery already calls the tool from Python; the Tool class isn’t driving an agent loop |
| `SmolagentsInstrumentor` in `main.py` | Only needed while smolagents is in the path |
| Duplicate LLM entrypoints | `complete_chat_json` vs `complete_job_discovery_chat_json` are nearly the same; leave until graph works, then maybe one helper |
| Stage 3 as one fat `run_stage3` | Fine for v1; leave split only if state fields make the graph clearer |

Keep: schema validation, URL filters, aptitude fit ranking, prompt loading, input safety—those are product logic, not framework noise.

## What “done” looks like for the first cut

- Same API behavior (`POST /v1/pipeline`, same JSON)
- One compiled `StateGraph` owning stage order
- Stage modules still readable without knowing LangGraph
- No new branching unless product needs it

Official docs for the primitives you’ll use: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
