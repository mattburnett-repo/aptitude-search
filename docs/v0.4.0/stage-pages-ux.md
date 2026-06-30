# Stage pages UX — one screen at a time

> **Status (v0.4.0):** Done. Shipped as the **presentation-only wizard** (option A below): one `POST /v1/pipeline`, five result steps after Running, Back/Next/Start over, panels stay mounted when navigating. Inference confidence is its own step (Step 2); occupation matches and role family plan are separate steps (3 and 4). Optional constraints UI remains commented out; pipeline still sends defaults. This file is kept mostly for archival reasons — the pre-ship planning notes below are no longer authoritative.

## What you have now

One long page: input → Go → progress log → **all four result panels stacked** when done (`App.tsx` lines 144–150).

## What you're describing

A **linear flow** — one screen at a time:

```
1. Input     → resume + constraints + Go
2. Running   → "Working on Stage 1…" (or 2 / 3)
3. Stage 1   → aptitude profile only
4. Stage 2   → O*NET matches + role family plan
5. Stage 3   → verified job matches
```

Back / Next (or "Continue") between result screens. Header can stay; the **main content** is one stage.

That's a **wizard**, not dots-and-checkmarks — same idea, less chrome.

## Two ways to build it

### A. **Presentation-only** (easiest — good first pass)

- Still one `POST /v1/pipeline` (full run).
- While loading: show **Running** page with progress (maybe mapped to "Stage 1 / 2 / 3" from message text).
- When `result` arrives: hide input, show **page 1** (aptitude only).
- User clicks **Next** → page 2 → page 3.
- **Back** revisits earlier pages; optional **Start over** resets.

**Pros:** No API changes; reuse existing `*Display` components.  
**Cons:** User waits through the whole pipeline before seeing Stage 1; long quiet gaps still happen behind one "Running" screen.

### B. **True stage-at-a-time** (better UX, more work)

- Call `/v1/stages/1`, then `/v1/stages/2`, then `/v1/stages/3` (or stream + emit partial results).
- Show each result page **as that stage finishes**.

**Pros:** Stage 1 visible in ~1 min; matches mental model.  
**Cons:** Three requests, state to pass between stages, error handling per stage; slightly different from today's single "Go".

## Practical recommendation

Start with **A** if you want quick UX win on [aptitude-search.vercel.app](https://aptitude-search.vercel.app/):

| Page | Content |
|------|--------|
| `input` | Current resume + constraints + Go |
| `running` | Single focused view + progress (derive stage from messages like `"Stage 2:"`) |
| `stage1` | `AptitudeProfileDisplay` + Next |
| `stage2` | `OccupationMatchesDisplay` + `RoleFamilyPlanDisplay` + Next |
| `stage3` | `VerifiedMatchesDisplay` + Start over |

Minimal state: `view: 'input' | 'running' | 'stage1' | 'stage2' | 'stage3'`.

Move to **B** later if "Running" for 5–10 minutes still feels wrong.

## Small UX details that help

- On **Running**, show **one line**: "Stage 2 of 3 — Matching to O*NET…" (parse from latest progress message).
- Hide the subtitle bullet list on result pages — less clutter.
- **Start over** always returns to `input` and clears `result`.

When you're ready to build, choose **A (wizard over full pipeline)** or **B (real per-stage API)** — A is the natural first slice.
