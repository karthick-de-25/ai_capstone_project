# ADR-0003: Human-in-the-Loop via LangGraph `interrupt`/`Command`

**Status:** Accepted

**Date:** 2026-03-15

## Context

The capstone requires at least one human-in-the-loop checkpoint for critical decisions or outputs. Our pipeline gates Recommendation Agent execution behind human approval.

Options considered:

1. **LangGraph `interrupt`/`Command`** — native StateGraph mechanism
2. **Separate REST endpoint** — run as web service, human approves via HTTP
3. **State flag polling** — set `needs_approval=True`, external loop polls and resumes

## Decision

Use LangGraph's built-in **`interrupt`** function and **`Command`** class for the HITL checkpoint.

- The `human_checkpoint` node calls `interrupt(...)` with the information the human needs (analysis + summary)
- The pipeline pauses automatically — no polling, no external state machine
- The human reviews and resumes via `Command(resume={"approved": True/False})`
- Thread-specific checkpoints via `MemorySaver` with `thread_id` parameter

## Consequences

- **Positive:** Zero infrastructure — no web server, no database, no external service
- **Positive:** Tight integration with LangGraph StateGraph — interrupt/resume is first-class
- **Positive:** Multiple threads (patients) can each have their own checkpoint state
- **Positive:** Works for both CLI demo and eventual Streamlit/Gradio UI
- **Negative:** Requires `MemorySaver` checkpointer (serializes state in memory)
- **Mitigation:** For production, swap to `SqliteSaver` or `PostgresSaver` for durable persistence; for the capstone, `MemorySaver` is sufficient

## Flow

```
Summary Agent ──▶ human_checkpoint [interrupt]
                         │
                         ├── human approves ──▶ Recommendation Agent
                         │
                         └── human rejects ──▶ END
```

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| REST endpoint | Adds network complexity; not needed for local demo |
| State flag polling | Would require an external loop watching state — fragile; interrupt is cleaner |
| CrewAI HITL | CrewAI has its own HITL mechanism, but we chose LangGraph for StateGraph flexibility |