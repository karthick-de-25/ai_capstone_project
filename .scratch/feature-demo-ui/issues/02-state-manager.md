# Issue 02: State Manager + Run Endpoint

**Type:** task
**Status:** resolved

## Goal

Create the in-memory pipeline state manager and wire up the `/run` POST handler to actually start the pipeline and handle the interrupt lifecycle.

## Files

| File | Action | Lines |
|------|--------|-------|
| `src/ui/state.py` | create | ~140 |
| `src/ui/app.py` | edit | ~30 |
| `src/ui/templates/index.html` | edit | ~10 |

## Done

- `StateManager` with `start_thread()`, `resume_thread()`, `get_thread()`
- Handles LangGraph interrupts across HTTP requests using `Command(resume=...)`
- `/run` redirects to `/status/<thread_id>`
- State survives across requests via module-level dict