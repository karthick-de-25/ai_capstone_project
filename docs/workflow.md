# Workflow Orchestration

## Architecture

The AI Clinical Report Summarization Assistant uses LangGraph **1.x** (`@entrypoint` + `@task` decorators) to orchestrate a sequential 3-agent pipeline with conditional routing and human-in-the-loop.

> **API note:** this project uses LangGraph 1.x (pinned in `requirements.txt`). The decorator
> style (`@entrypoint`/`@task`) replaces the legacy `StateGraph`/`add_node`/`add_edge` API
> from 0.2–0.3.x. Control flow (sequencing, routing) is ordinary Python inside the
> entrypoint; `interrupt()`/`Command(resume=...)` provides the human checkpoint.

## Core Flow

```
START
  │
  ▼
[Agent 1: analyze_report] ── report_text → analysis
  │
  ▼
[classify_patient] ── normal ──▶ return early
  │ abnormal
  ▼
[Agent 2: generate_summary] ── analysis → summary
  │
  ▼
[interrupt → human approves] ── rejected ──▶ return early
  │ approved
  ▼
[Agent 3: generate_recommendations] ── analysis + summary → recommendations
  │
  ▼
END
```

### Conditional Branches

| Condition | Route | Rationale |
|-----------|-------|-----------|
| `classification == "normal"` | Return early (no summary/recommendations) | No abnormalities to follow up on |
| `classification == "abnormal"` | Continue to Summary Agent | Standard path |
| `classification == "critical"` | Alert human (separate flow) | Requires immediate clinician attention |
| Human rejects recommendations | Return early | Clinician disagrees — stop |
| Task failure (retries exhausted) | Raises → propagates | Treated as an API/LLM error, surfaced to caller |

## Pipeline Definition

```python
# src/pipeline/pipeline.py
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy, interrupt

from .agents.summary import generate_summary
from .agents.analysis import analyze_report, classify_patient
from .agents.recommendation import generate_recommendations
from .contracts import PipelineInput, PipelineOutput


@entrypoint(checkpointer=InMemorySaver())
def pipeline(report: PipelineInput) -> PipelineOutput:
    # Agent 1 (parallel-ready: launch, then await)
    analysis_future = analyze_report(report["report_text"])
    analysis = analysis_future.result()

    # Classifier — plain Python, no separate node needed
    patient_class = classify_patient(analysis)
    if patient_class == "normal":
        return PipelineOutput(analysis=analysis, summary="", recommendations=[])

    # critical → alert human via interrupt (alternative flow)
    if patient_class == "critical":
        alert = interrupt({"level": "critical", "analysis": analysis})
        if not alert.get("approved", False):
            return PipelineOutput(analysis=analysis, summary="", recommendations=[])

    # Agent 2
    summary = generate_summary(analysis).result()

    # Human-in-the-loop checkpoint (Agent 3 is gated on approval)
    review = interrupt({"question": "Approve recommendations?", "analysis": analysis, "summary": summary})
    if not review.get("approved", False):
        return PipelineOutput(analysis=analysis, summary=summary, recommendations=[])

    # Agent 3
    recommendations = generate_recommendations(analysis, summary).result()
    return PipelineOutput(analysis=analysis, summary=summary, recommendations=recommendations)
```

## Agent Tasks

```python
# src/pipeline/agents/analysis.py
from langgraph.func import task
from langgraph.types import RetryPolicy

@task(retry_policy=RetryPolicy(max_attempts=3))
def analyze_report(report_text: str) -> str:
    """Agent 1: extract key findings + abnormal values."""
    ...

def classify_patient(analysis: str) -> str:
    """Plain helper — returns 'normal' | 'abnormal' | 'critical'."""
    ...

# src/pipeline/agents/summary.py
@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_summary(analysis: str) -> str:
    """Agent 2: concise structured clinical summary."""
    ...

# src/pipeline/agents/recommendation.py
@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_recommendations(analysis: str, summary: str) -> list[str]:
    """Agent 3: 3-5 actionable follow-up recommendations."""
    ...
```

## Human-in-the-Loop Checkpoint

Implemented via `interrupt()` + `Command(resume=...)`:

1. Pipeline runs through `generate_summary`
2. `interrupt({...})` raises `GraphInterrupt`, pausing execution; the payload is surfaced to the client
3. Human reviews analysis + summary and decides
4. Resume with `Command(resume={"approved": True/False})`

```python
# Run the graph (e.g., from a REPL or CLI): first invocation hits the interrupt
config = {"configurable": {"thread_id": "patient-001"}}
for chunk in pipeline.stream({"report_text": report_text}, config):
    print(chunk)
# → {'__interrupt__': (Interrupt(value={'question': ...}, id='...'),)}

# Human approves → resume
result = pipeline.invoke(Command(resume={"approved": True}), config)
```

Key facts (verified against langgraph 1.2.11):
- `interrupt` requires a checkpointer — pass `checkpointer=InMemorySaver()` to `@entrypoint`
- The payload is surfaced as `{'__interrupt__': (Interrupt(value=..., id=...),)}`
- Resuming re-executes the entrypoint, but completed `@task` results are cached by the checkpointer (`InMemorySaver`) — they are *not* re-run
- `Command` supports `resume=`, `update=`, `goto=`, and `graph=`

## Parallel Execution

Tasks are async-friendly by default. Launch all futures before awaiting:

```python
# Fan-out: analyze each section in parallel
futures = [analyze_section(section) for section in sections]
results = [f.result() for f in futures]  # all run concurrently
```

Or in the RAG layer (LangChain 1.x LCEL):

```python
from langchain_core.runnables import RunnableParallel

rag_chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    | prompt
    | llm
    | StrOutputParser()
)
```

## Error Handling & Retries

- `@task(retry_policy=RetryPolicy(max_attempts=3))` retries transient failures (network,
  rate-limit) with exponential backoff before giving up
- Exceptions propagate to the entrypoint caller once retries are exhausted
- `RetryPolicy` fields: `max_attempts` (default 3), `initial_interval`, `backoff_factor`,
  `max_interval`, `jitter`, `retry_on` (exception types/callable)
- Not all errors should retry: set `retry_on=(TimeoutError, RateLimitError)` explicitly so
  invalid-input errors (e.g. `ValueError`) fail fast

## Logging & Monitoring

Every agent task logs via Python's `logging` module:

```python
import logging
log = logging.getLogger(__name__)

@task
def analyze_report(report_text: str) -> str:
    log.info("Agent 1: Analyzing report...")
    result = llm.invoke(prompt)
    log.info("Agent 1: complete (%d chars)", len(result.content))
    return result.content
```

Logged events: task entry/exit, classification result, interrupt triggered/resumed,
retries, pipeline completion.