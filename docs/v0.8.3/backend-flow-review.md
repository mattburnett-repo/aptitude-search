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

## Done (this pass)

- Extracted `exception_handlers`, `logging_setup`, `observability` from `main.py`.
- Unified resume ingress (`ingest_resume` / `prepare_pipeline_inputs`); pipeline no longer double-runs safety.
- Moved Stage 2 into `pipeline.py`; removed `role_family_plan.py`.
- Simplified `llm.py` chat call; renamed wrappers to `aptitude_llm_call` / `job_discovery_llm_call`.
- Added stage payload aliases (`AptitudeProfile`, `RoleFamilyPlan`, `VerifiedMatches`, …).
- Docstrings/comments on stages, discovery, LLM wrappers; `/health` returns `version`.
- **Part A.1 dead paths:** removed duplicate empty-plan `adjacent_roles` line; aptitude-fit “no role family alignment” now hard-rejects (`score = -1`); dropped unused Stage 1 `INPUT TEMPLATE`; corrected stale `aptitude_fit_min_*` docs to `result_top_k`.
- **Part A.2 repeated structure:** `_family_string_list` in `aptitude_fit.py`; single Tavily `search` kwargs path; `labeled_names` imported from `profile_text` in synthesis.

---

## Part A — Remaining code simplification

### 1. Clear bugs / dead paths

_Done — see above._

### 2. Repeated structure worth collapsing

_Done — see above._

### 3. Complexity that exists because Stage 1 is sloppy

`normalize_aptitude_profile` in `validate.py` is a large compatibility layer:

- `name` ↔ `label` swaps
- inverted `confidence_map` (`{high: [...]}` vs `{field: {confidence, reason}}`)
- seniority aliases

Simplify this **after** (or together with) prompt/schema tightening. Until then, deleting normalizers will just raise validation failures.

### 4. Smaller cleanups (optional)

- `main.py` OpenAPI tags look malformed (`"Health check"` / `"Full pipeline"` as keys instead of `"description"`).
- `profile_labels` used on plain-string `search_terms` works via the string branch; a dedicated helper would be clearer.

**Not worth “simplifying” right now:** input_safety (Presidio), streaming queue, URL filters — they earn their size.

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

### Prompt problems to revisit

1. **Schema vs prompt conflict**  
   Prompt: empty arrays / `"unknown"` when uncertain.  
   Schema: `core_skills` and `strengths` `minItems: 1`, `rationale` `minItems: 1`, `aptitude_summary` `minLength: 20`.  
   Model is told it may empty fields that validation will reject.

2. **“SHARED VOCABULARY (USED BY BOTH PROMPTS)”**  
   Full defs live only in Prompt 1. Prompt 2 has none. Prompt 3 has a short locked subset. Either share one vocabulary block or drop the “both prompts” claim.

3. **`name` vs `label`**  
   Repeated in system prompt + user task; still needs a normalizer. Options: unify schema to one key, or keep split but make the prompt shorter and rely on schema examples.

4. **Evidence rules are uneven**  
   Detailed `evidence_from_resume` rules are skills-only; schema allows evidence on labeled items too. Decide: evidence everywhere, or skills-only and say so in schema/`$defs`.

5. **Tension: non-obvious adjacent roles vs no invention**  
   “Include at least one non-obvious but justified role” vs “No aspirational.” That’s the product heart of Stage 1 — worth rewriting as a crisp rule (e.g. must cite skill overlap / progression / known path in `evidence_from_resume`).

6. **Redundancy / dead text**  
   JSON-only rules repeated; unused `INPUT TEMPLATE`; “v4” title with no contract versioning; processing steps overlap vocabulary.

7. **`confidence_map` under-specified relative to failure modes**  
   Normalizer handles inverted maps and string values → prompt examples should match schema exactly so that code can shrink.

### Prompt redesign direction (recommendation, not implementation)

Prioritize quality of fields that drive the rest of the pipeline:

1. `strengths` + `working_style_signals` (fit + embed)
2. `adjacent_roles` (Stage 2 / discovery / fit)
3. `aptitude_summary` (embed + UI)
4. Then skills/domains as supporting, not primary

Align empty-vs-required with the schema. Cut dead template. Make vocabulary once and reference it. Tighten adjacent-role justification so “non-obvious” doesn’t become invention.

---

## Suggested order for remaining work

1. **Stage 1 prompt + schema alignment** (biggest leverage on profile quality *and* later code shrink)
2. **Optional small cleanups** (OpenAPI tag keys, `profile_labels` for plain search_terms)
3. **Only then** thin `normalize_aptitude_profile` once the model reliably emits shape
