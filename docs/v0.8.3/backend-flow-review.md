# Backend flow review — simplification & aptitude profile prompts

Review of the entire backend flow: code simplification candidates, plus revisiting aptitude profile extraction/creation (prompt-focused).

## Flow (what actually runs)

```text
resume → prepare_pipeline_inputs / ingest_resume (extract → safety/PII)
      → Stage 1 LLM → AptitudeProfile (+ normalize + schema)
      → Stage 2: O*NET embed match → RoleFamilyPlan LLM  (in pipeline.py)
      → Stage 3: discovery queries → Tavily → aptitude_fit rank → synthesis LLM
      → verified_matches
```

Core wiring: `pipeline.py` (stages 1–3) → `job_discovery/{discovery,aptitude_fit,synthesize_verified_matches}.py`.

Resume ingress: `resume_io.py` (`extract_resume_text` → `ingest_resume` → `prepare_resume` in `input_safety.py`).

---

## Part A — Code simplification — done

### Wiring / structure (earlier in this pass)

- Extracted `exception_handlers`, `logging_setup`, `observability` from `main.py`.
- Unified resume ingress (`ingest_resume` / `prepare_pipeline_inputs`); pipeline no longer double-runs safety.
- Moved Stage 2 into `pipeline.py`; removed `role_family_plan.py`.
- Simplified `llm.py` chat call; renamed wrappers to `aptitude_llm_call` / `job_discovery_llm_call`.
- Added stage payload aliases (`AptitudeProfile`, `RoleFamilyPlan`, `VerifiedMatches`, …).
- Docstrings/comments on stages, discovery, LLM wrappers; `/health` returns `version`.

### A.1 Clear bugs / dead paths

- Removed duplicate empty-plan `adjacent_roles` line.
- Aptitude-fit “no role family alignment” hard-rejects (`score = -1`).
- Dropped unused Stage 1 `INPUT TEMPLATE`.
- Corrected stale `aptitude_fit_min_*` docs → `result_top_k`.

### A.2 Repeated structure

- `_family_string_list` in `aptitude_fit.py`.
- Single Tavily `search` kwargs path.
- `labeled_names` from `profile_text` in synthesis.

### A.3 Stage 1 shape (prompt + thinner normalizer)

**Prompt / user task** (`prompts/01-resume-to-aptitude-profile.md`, `prompts/stage1-agent-user-task.txt`):

- Matches schema minimums: `core_skills` / `strengths` / `rationale` non-empty; other lists may be `[]`.
- Exact `seniority_band` enum (no aliases in the prompt).
- Correct vs wrong `confidence_map` examples (field → `{confidence, reason}`).

**`normalize_aptitude_profile`** (`backend/app/core/validate.py`):

- No `name`↔`label` swaps (wrong key → schema failure).
- No inverted `{high: [fields]}` rewrite.
- Remaining light cleanup: prune extras, coerce item confidence, string→`{confidence,reason}` entries, `mid-level`→`mid` alias.

### A.4 Smaller cleanups

- `main.py` OpenAPI tags use `"description"`.
- `profile_text.py`: `profile_labels` / `labeled_names` for skill/labeled objects; `string_list` / `joined_strings` for plan plain-string arrays (`search_terms`, `work_modes`, `avoid_terms`). Call sites: discovery, synthesis context, `_family_string_list`.

**Left alone on purpose:** input_safety (Presidio), streaming queue, URL filters.

---

## Part B — Aptitude profile (prompt-focused) — open

Stage 1 prompt: `prompts/01-resume-to-aptitude-profile.md`. User preamble: `prompts/stage1-agent-user-task.txt`.

### What Stage 1 output is actually used for

From product direction (`docs/v0.2.0/aptitude_refinement/`) and code:

| Field | Discovery | Fit ranking | O*NET embed | Synthesis |
|--------|-----------|-------------|-------------|-----------|
| `core_skills` / `secondary_skills` | fallback only | no | **no** | yes (compact) |
| `adjacent_roles` | via Stage 2 / fallback | yes | yes | yes |
| `strengths` / `working_style_signals` | no | **yes** | yes | yes |
| `aptitude_summary` | no | no | yes | yes |
| `domains` | fallback | no | no | yes |
| `confidence_map` / `rationale` / evidence | mostly display / audit | no | no | no |

So the prompt still spends a lot of weight on **skills taxonomy**, while matching/search care most about **work patterns + adjacent roles + summary**.

### Prompt problems still open

1. **“SHARED VOCABULARY (USED BY BOTH PROMPTS)”**  
   Full defs live only in Prompt 1. Prompt 2 has none. Prompt 3 has a short locked subset. Either share one vocabulary block or drop the “both prompts” claim.

2. **`name` vs `label`**  
   Prompt + user task still teach the split; normalizer no longer swaps. Options: unify schema to one key, or shorten the teaching text and rely on schema.

3. **Evidence rules are uneven**  
   Detailed `evidence_from_resume` rules are skills-only; schema allows evidence on labeled items too. Decide: evidence everywhere, or skills-only and say so in schema/`$defs`.

4. **Tension: non-obvious adjacent roles vs no invention**  
   “Include at least one non-obvious but justified role” vs “No aspirational.” Worth a crisp rule (e.g. must cite skill overlap / progression / known path in `evidence_from_resume`).

5. **Redundancy / dead text**  
   JSON-only rules repeated; “v4” title with no contract versioning; processing steps overlap vocabulary. (`INPUT TEMPLATE` already removed in A.1.)

### Fixed earlier (A.3) — keep for context

- Schema vs prompt empty-array conflict.
- Underspecified `confidence_map` (inverted-map failure mode).

### Prompt redesign direction (recommendation, not implementation)

Prioritize quality of fields that drive the rest of the pipeline:

1. `strengths` + `working_style_signals` (fit + embed)
2. `adjacent_roles` (Stage 2 / discovery / fit)
3. `aptitude_summary` (embed + UI)
4. Then skills/domains as supporting, not primary

Cut redundant prompt text. Make vocabulary once and reference it. Tighten adjacent-role justification so “non-obvious” doesn’t become invention.

---

## Suggested order for remaining work

1. **Stage 1 prompt quality (Part B)** — vocabulary claim, evidence rules, adjacent-role tension, prioritize strengths / working_style / adjacent_roles / summary
2. Drop remaining `mid-level` seniority alias once live Stage 1 outputs are clean
