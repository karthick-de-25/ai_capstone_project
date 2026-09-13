# ADR-0003: Human-in-the-Loop via LangGraph `interrupt`/`Command`

**Status:** Accepted

**Date:** 2026-03-15

## Context

The capstone requires at least one human-in-the-loop checkpoint for critical decisions or outputs. Our pipeline gates Recommendation Agent execution behind human approval.

Options considered:

1. **LangGraph `interrupt`/`Command`** — native LangGraph 1.x mechanism
2. **Separate REST endpoint** — run as web service, human approves via HTTP
3. **State flag polling** — set `needs_approval=True`, external loop polls and resumes

## Decision

Use LangGraph's built-in **`interrupt`** function and **`Command`** class for the HITL checkpoint.

- The entrypoint calls `interrupt({...})` with the information the human needs (analysis + summary)
- The pipeline pauses automatically (raises `GraphInterrupt`) — no polling, no external state machine
- The human reviews and resumes via `Command(resume=...)`
- Thread-specific checkpoints via `InMemorySaver` + `thread_id` in the run config
- `interrupt` requires a checkpointer; completed `@task` results are cached across the resume (not re-run)

## Consequences

- **Positive:** Zero infrastructure — no web server, no database, no external service
- **Positive:** Tight integration with LangGraph 1.x — interrupt/resume is first-class in `@entrypoint`
- **Positive:** Multiple threads (patients) can each have their own checkpoint state
- **Positive:** Works for both CLI demo and eventual Streamlit/Gradio UI
- **Negative:** Requires a checkpointer (default: `InMemorySaver` serializes state in memory)
- **Mitigation:** For durable persistence, install `langgraph-checkpoint-sqlite` (`AsyncSqliteSaver`) or `langgraph-checkpoint-postgres` (`AsyncPostgresSaver`); for the capstone, `InMemorySaver` is sufficient

## Flow

```
generate_summary ──▶ interrupt({analysis, summary})
                            │
                            ├── resume(approved=True)  ──▶ generate_recommendations
                            │
                            └── resume(approved=False) ──▶ return early
```

## Code Sketch (verified against langgraph 1.2.11)

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint
from langgraph.types import Command, interrupt

@entrypoint(checkpointer=InMemorySaver())
def pipeline(report: PipelineInput) -> PipelineOutput:
    analysis = analyze_report(report["report_text"]).result()
    summary = generate_summary(analysis).result()
    review = interrupt({"question": "Approve recommendations?", "analysis": analysis, "summary": summary})
    if not review.get("approved", False):
        return PipelineOutput(analysis=analysis, summary=summary, recommendations=[])
    recommendations = generate_recommendations(analysis, summary).result()
    return PipelineOutput(analysis=analysis, summary=summary, recommendations=recommendations)

# Run: hits interrupt
for chunk in pipeline.stream({...}, {"configurable": {"thread_id": "patient-001"}}):
    ...
# Resume:
result = pipeline.invoke(Command(resume={"approved": True}), config)
```

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| REST endpoint | Adds network complexity; not needed for local demo |
| State flag polling | Would require an external loop watching state — fragile; interrupt is cleaner |
| CrewAI HITL | CrewAI has its own HITL mechanism, but we chose LangGraph 1.x `interrupt`/`Command` for plain-Python orchestration flexibility |