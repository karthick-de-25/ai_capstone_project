# Feature Spec: Demoable Flask UI

## Goal

Replace the current CLI-only entry point (`python src/main.py`) with a web-based UI that makes the pipeline demoable to stakeholders. The UI must handle:

- Report input (paste text or load a synthetic report)
- Visual pipeline progress (Analysis → Classification → Summary → Recommendations)
- Human-in-the-loop interrupts (approve/reject checkpoints)
- Nicely formatted results (analysis, summary, recommendations)
- Multi-report memory (chain reports for the same patient)

## Constraints

- Flask (lightweight, no async requirement, Python-native)
- Minimal new dependencies — `flask` only (maybe `flask-wtf` if forms are needed)
- Pipeline state must survive across HTTP requests (LangGraph interrupts cannot be handled in a single request)
- No real patient data — synthetic data only
- No cloud deployment — runs locally

## Design Sketch

```
/ (index)          → landing page: report input + "Run" button
/run               → start pipeline (POST) → redirect to /status/<thread_id>
/status/<id>       → show current state (pending/interrupt/complete) with results
/resume/<id>       → resume after interrupt (POST approval)
/synthetic         → generate a synthetic report (any variant) → populate input
```

### State Model

A simple in-memory dict (`thread_id → ThreadState`) maps each UI session to pipeline execution:

```python
@dataclass
class ThreadState:
    thread_id: str
    report_text: str
    previous_summary: str | None
    status: Literal["running", "interrupt", "complete", "error"]
    interrupt_payload: dict | None  # the interrupt data to show user
    output: PipelineOutput | None   # final result
    error: str | None
```