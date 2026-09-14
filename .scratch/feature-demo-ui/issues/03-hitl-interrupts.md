# Issue 03: HITL Interrupt Handling

**Type:** task
**Status:** resolved

## Goal

Handle LangGraph `interrupt()` calls across HTTP requests — display interrupt payloads and let the user approve/reject.

## Files

| File | Action | Lines |
|------|--------|-------|
| `src/ui/app.py` | edit | ~20 |
| `src/ui/templates/status.html` | create | ~100 |

## Done

- `/status/<thread_id>` GET displays interrupt payload (critical alert vs recommendation approval)
- `/resume/<thread_id>` POST resumes pipeline with `Command(resume={"approved": True/False})`
- Handles both the critical alert checkpoint and the recommendation approval checkpoint
- Multi-interrupt path (critical → approve → summary → recommendations interrupt) supported