# Input safety — PII deletion and prompt-injection gate

> **Status (v0.5.0):** Implemented. Resume ingress runs injection screening (regex → blocklist → Prompt Guard 2 22M) then Presidio PII deletion before Stage 1.

## Problem

User-supplied resume text can contain:

- **PII** — email, phone, address, etc. — that should not be sent to LLMs or retained in logs unchanged.
- **Prompt injection** — instructions embedded in pasted text or PDF extract meant to override system behavior.

## Approach

Two tracks: **delete PII** (after injection checks) and **block injection** (cheap checks first, classifier last).

### PII — delete, don’t replace

Redaction placeholders inflate token count. v0 **deletes** matches instead of substituting tags like `[EMAIL_REDACTED]`.

**Tool: [Microsoft Presidio](https://github.com/microsoft/presidio)** (MIT, no license fee). Dev time and compute to run it locally are acceptable costs for v0 — there is no per-call vendor charge; you pay in engineering and a small CPU hit per resume.

- **Presidio analyzer + anonymizer** — detect entities, then **remove** spans (not mask/replace). Configure entity types for v0, e.g. email, phone, person name, location, US SSN.
- **Optional contact-block heuristic** — drop obvious header/footer contact lines before or after Presidio.
- **Regex stays for injection**, not as the primary PII layer — Presidio already includes pattern recognizers for structured IDs; hand-rolled regex is redundant for email/phone once Presidio is in place.

**Tuning:** NER can false-positive on resume text (company names, cities, tech terms). Validate on [`fixtures/sample-resumes/`](../../fixtures/sample-resumes/) and adjust entity list or confidence thresholds before shipping.

Net effect: same or **fewer** tokens downstream; aptitude still has skills, roles, and employers.

### Injection — block cascade

Run on **original** text **before** PII deletion so attacks hidden in contact blocks are not stripped first.

1. **Regex** — fake system tags, obvious override patterns.
2. **Phrase blocklist** — known jailbreak / instruction-override strings.
3. **`meta-llama/Llama-Prompt-Guard-2-22M`** — purpose-built classifier (`benign` / `malicious`); not a chat model.

Any step in the injection chain that flags input → **400** with the shared user message ([Error responses and frontend](#error-responses-and-frontend)).

#### Prompt Guard integration

- Model: `meta-llama/Llama-Prompt-Guard-2-22M` (English resumes; use 86M if multilingual is required later).
- **512-token context window** — chunk resume into segments (~400 tokens each); fail if **any** chunk is `malicious`.
- Integration via **text-classification** (HF inference or local `transformers` pipeline), **not** the existing `aptitude_llm_call` / `job_discovery_llm_call` chat path used by aptitude and job discovery.
- Regex and blocklist run first to reduce classifier calls and cost.

### Also (not ingress gates)

- **Prompt hardening** — keep resume in `<resume>` delimiters; aptitude and discovery system prompts treat resume as untrusted data and ignore instructions inside it.
- **Output schema validation** — jsonschema on stage outputs (already in place); last line of defense on malformed or off-task model output.

## Flow

```text
resume in (paste or PDF extract)
  → injection: regex → blocklist → Prompt Guard 2 22M (chunked)   [fail → 400]
  → PII: Presidio delete (+ optional contact-block strip)
  → Stage 1 → Stage 2 → Stage 3
```

Entry point: after PDF extract in `parse_pipeline_body` / start of `run_pipeline`, before Stage 1.

## Error responses and frontend

Injection failures use the **same HTTP error path** as existing resume validation (e.g. invalid PDF in `resume_io.py`). No new frontend API shape for v0.

### Backend

- Raise `HTTPException(status_code=400, detail=INPUT_REJECTED_MESSAGE)` from the injection cascade (regex, blocklist, or Prompt Guard — **one shared user-facing string** for all three).
- Do **not** include matched patterns, blocklist hits, classifier scores, or resume excerpts in `detail` (avoid leaking attack content or aiding evasion). Log the reason server-side only (`logger.warning` with a short code, e.g. `injection_blocklist`).
- Suggested copy (single constant in `input_safety.py`):

  ```text
  We couldn't process this resume. Check the file and try again, or paste plain text instead.
  ```

**Existing handlers (no changes required for basic UX):**

- Non-stream `POST /v1/pipeline` — `main.py` `http_exception_handler` → JSON `{ "detail": "...", "request_id": "..." }`.
- Stream `POST /v1/pipeline?stream=1` — `stream_pipeline.py` catches `HTTPException` → NDJSON `{ "type": "error", "detail": "...", "request_id": "..." }`.

### Frontend

**Already wired** — no v0 UI work unless copy or styling is refined later:

- `frontend/src/api/pipeline.ts` — reads `detail` (+ optional `request_id`) from HTTP body or stream error event.
- `frontend/src/hooks/usePipeline.ts` — sets `error` state on failure.
- `frontend/src/App.tsx` — shows `<p className="error">{error}</p>` on the input view and returns the user there when the run fails.

The user sees the generic message plus `(ref: …)` when the backend sends a `request_id`.

### Tests

- Mocked API test: malicious resume → **400**, `detail` equals the shared constant (not attack-specific text).
- Stream test: same `detail` on `{ "type": "error" }` event.

## Config

New section, separate from aptitude and job discovery:

```toml
[llm.input_guard]
model_key = ""  # Hugging Face key
model = "meta-llama/Llama-Prompt-Guard-2-22M"
```

| Config block           | Model role                          |
| ---------------------- | ----------------------------------- |
| `[llm.input_guard]`    | Injection classifier (22M)          |
| `[llm.aptitude]`       | Stage 1 + 2 reasoning (70B)         |
| `[llm.job_discovery]`  | Stage 3 synthesis (70B)             |

## Fixtures and tests

**Input text** (`fixtures/sample-resumes/`):

- Reuse a clean resume (e.g. `career-changer-mixed-stack.txt`) — guard should pass; Presidio should strip contact PII without removing job content.
- Add at least one malicious resume (e.g. `prompt-injection-ignore-instructions.txt`) — guard should block.
- Optional: resume with known name/email/phone in header — unit test that Presidio deletion removes them and leaves experience bullets intact.

**Golden outputs** (`fixtures/example-outputs/`):

- `input-guard-clean-pass.json` — normalized pass verdict for mocked tests.
- `input-guard-injection-detected.json` — normalized block verdict for mocked tests.

Register in `config.toml` / `config.test.toml` for `scripts/validate_fixtures.py` against a new `input-guard.schema.json`.

**Tests** (mocked, offline — same pattern as `test_pipeline_mocked.py`):

- Schema accepts golden fixtures.
- Mock classifier / guard layer: clean input → pipeline continues; blocked input → **400** with shared `detail` (see [Error responses and frontend](#error-responses-and-frontend)).
- Optional: `fixtures/pipeline-request-injection-test.json` for manual Swagger checks.

Mocked tests prove wiring and schema; live Prompt Guard accuracy is a separate spot-check (like Stage 3 quality today).

## Implementation touchpoints (reference)

- `backend/app/core/resume_io.py` — extract text; run safety pipeline.
- `backend/app/core/input_safety.py` (or similar) — injection cascade + Presidio PII deletion; `INPUT_REJECTED_MESSAGE` constant; raise `HTTPException(400, …)` on block.
- `backend/app/core/llm.py` — new classification helper for Prompt Guard (not `aptitude_llm_call`).
- `backend/app/core/config.py` — `LlmInputGuardSettings`; optional Presidio entity/threshold config.
- `backend/app/pipeline.py` — call guard before `run_stage1`.
- `backend/requirements.txt` — `presidio-analyzer`, `presidio-anonymizer`, and spaCy model dep for NER.
- `prompts/` — optional guard user-task only if a chat fallback is added later; Prompt Guard needs no prompt file.
