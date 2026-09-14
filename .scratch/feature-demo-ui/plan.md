# Plan: Demoable Flask UI

## Overview

Replace the CLI entry point with a Flask web UI. The pipeline code itself stays unchanged — the UI wraps it with an HTTP layer that handles LangGraph interrupts across multiple requests.

## Step Sizing

| Step | Files | Δ Lines | Outcome |
|------|-------|---------|---------|
| 1. Scaffold Flask app, routes, templates | 3 | ~80 | App runs, renders index page |
| 2. Run pipeline statefully across requests | 3 | ~140 | Reports can be submitted, pipeline starts |
| 3. HITL interrupt handling (approve/reject) | 2 | ~100 | User can approve/reject checkpoints from UI |
| 4. Results display + synthetic report loader | 2 | ~90 | Full flow visible; synthetic reports selectable |
| 5. Multi-report memory chaining + polish | 2 | ~80 | Chain reports for same patient; nice styling |

**Total: ~490 lines**

---

### Step 1: Scaffold Flask App, Routes & Templates
- **Goal:** Get Flask serving the index page with a report input form.
- **Files:**
  - `src/ui/__init__.py` (empty — package marker)
  - `src/ui/app.py` (Flask app factory, `__init__` config)
  - `src/ui/templates/index.html` (form with textarea + submit)
  - `requirements.txt` (add `flask>=3.0`)
- **Changes:** ~80 lines (3 new files, 1 edit).
- **Review:** Does the form render? Does POST `/run` have a stub handler?
- **Done:** `flask run` shows a page with a big textarea and a "Run Pipeline" button.

### Step 2: State Manager + Run Endpoint
- **Goal:** Submit a report → start the pipeline → display progress.
- **Files:**
  - `src/ui/state.py` (in-memory `ThreadState` dataclass + `StateManager`)
  - `src/ui/app.py` (add `/run` POST handler that invokes pipeline and stores state)
  - `src/ui/templates/index.html` (update to show thread status after submit)
- **Changes:** ~140 lines (1 new, 2 edits).
- **Review:** Does the pipeline start? Does state survive the redirect?
- **Done:** Submitting a report creates a thread, runs pipeline until interrupt (or completion), and redirects to status page.

### Step 3: HITL Interrupt Handling
- **Goal:** Display interrupt questions to the user and resume the pipeline.
- **Files:**
  - `src/ui/app.py` (add `/status/<thread_id>` GET + `/resume/<thread_id>` POST)
  - `src/ui/templates/status.html` (show interrupt payload + approve/reject buttons; show results if done)
- **Changes:** ~100 lines (1 new template, 1 edit).
- **Review:** Does the interrupt payload display? Does clicking approve resume the pipeline and advance?
- **Done:** Full round-trip: submit → pipeline runs → hits interrupt → user clicks approve → pipeline continues → results shown.

### Step 4: Results Display + Synthetic Report Loader
- **Goal:** Nicely formatted results (analysis, summary, recommendations) and a way to generate synthetic reports from the UI.
- **Files:**
  - `src/ui/app.py` (add `/synthetic` GET that returns a generated report text; update status template)
  - `src/ui/templates/status.html` (display analysis/summary/recommendations with sections)
- **Changes:** ~90 lines (2 edits).
- **Review:** Are results readable? Can you generate a normal/abnormal/critical synthetic report?
- **Done:** Results page shows structured output; user can load any synthetic variant.

### Step 5: Multi-Report Memory Chaining + Polish
- **Goal:** Chain multiple reports for the same patient (memory demo) and polish the UI.
- **Files:**
  - `src/ui/app.py` (after complete, offer "Run another report" with same thread_id)
  - `src/ui/templates/status.html` (add "Run Another" button; show previous summary context)
- **Changes:** ~80 lines (2 edits).
- **Review:** Can you run 2+ reports and see "Trend vs Previous" in summaries?
- **Done:** Multi-report loop works; basic CSS makes it presentable.