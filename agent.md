# Agents — AI Clinical Report Summarization Assistant

## Overview

Three agents execute sequentially, orchestrated by a LangGraph 1.x `@entrypoint` calling `@task`-decorated functions. Each agent has a distinct role, system prompt, input/output contract, and error behavior.

---

## Agent 1: Report Analysis Agent

**Role:** Extract key findings, abnormal lab values, and notable observations from a raw clinical report.

**Owner:** Karthick

### Input

| Field | Type | Description |
|-------|------|-------------|
| `report_text` | `string` | Raw clinical report text (lab results, physician notes, patient info) |

### Output (returned to the entrypoint)

| Field | Type | Description |
|-------|------|-------------|
| `analysis` | `string` | Structured analysis: key findings, abnormal values, impressions |
| `classification` | `string` | Severity label: `normal`, `abnormal`, or `critical` (set by classifier logic in the entrypoint) |

### System Prompt

```
You are a clinical report analyst. Extract key findings, abnormal lab values,
and notable observations from this report. Be thorough but concise.

Report:
{report_text}
```

"""Agent 1 — return the analysis string; errors surface as an exception.
Classification is decided by the entrypoint after this returns."""

@task(retry_policy=RetryPolicy(max_attempts=3))
def analyze_report(report_text: str) -> str:
    ...

### Tests

- ✅ Parses a well-formed lab report → returns structured analysis
- ✅ Handles empty report text → graceful error message
- ✅ Handles LLM timeout → error appended, pipeline continues

---

## Agent 2: Summary Agent

**Role:** Produce a concise, structured clinical summary from the analysis output.

**Owner:** Raj

### Input

| Field | Type | Source |
|-------|------|--------|
| `analysis` | `string` | Output of Agent 1 |

### Output (returned to the entrypoint)

| Field | Type | Description |
|-------|------|-------------|
| `summary` | `string` | Structured summary: Key Findings → Abnormal Values → Clinical Impression |

### System Prompt

```
You are a clinical summary specialist. Produce a concise, structured summary
of the following analysis. Include:
- Key findings
- Abnormal values
- Clinical impressions

Analysis:
{analysis}
```

### Format Requirements

- Bullet-point structure
- Top 3-5 findings only
- Abnormal values **bolded** or marked with `⚠️`
- No new information — summarize only what's in the analysis

"""Agent 2 — return the summary string; errors surface as an exception."""

@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_summary(analysis: str) -> str:
    ...

### Tests

- ✅ Summarizes a multi-finding analysis → concise, 3-5 bullet format
- ✅ Handles analysis with no abnormal findings → "No abnormal findings"
- ✅ Handles LLM failure → fallback message

---

## Agent 3: Recommendation Agent

**Role:** Generate 3-5 actionable follow-up recommendations based on analysis and summary.

**Owner:** Mahesh

### Input

| Field | Type | Source |
|-------|------|--------|
| `analysis` | `string` | Output of Agent 1 |
| `summary` | `string` | Output of Agent 2 |

### Output (returned to the entrypoint)

| Field | Type | Description |
|-------|------|-------------|
| `recommendations` | `list[string]` | 3-5 numbered follow-up recommendations |

### System Prompt

```
You are a clinical recommendation specialist. Based on the analysis and summary,
provide 3-5 actionable follow-up recommendations.

Analysis:
{analysis}

Summary:
{summary}

Recommendations (one per line, prefixed with '-'):
```

### Format Requirements

- 3-5 recommendations
- Each prefixed with `- ` (parsed into list)
- Actionable, specific (not generic)
- Based **only** on the analysis + summary content

"""Agent 3 — return a list of recommendations; errors surface as an exception."""

@task(retry_policy=RetryPolicy(max_attempts=3))
def generate_recommendations(analysis: str, summary: str) -> list[str]:
    ...

### Tests

- ✅ Generates 3-5 recommendations for a diabetes + hypertension case
- ✅ Handles empty analysis + summary → generic fallback recommendation
- ✅ Handles LLM failure → fallback list

---

## Contract Schema (LangGraph 1.x)

LangGraph 1.x uses a decorator style — data flows through task arguments and return
values, so there is no mutable shared-state dict. The contracts live in
`src/pipeline/contracts.py`:

```python
from typing import TypedDict

class PipelineInput(TypedDict):
    """What enters the pipeline: one raw clinical report."""
    report_text: str

class PipelineOutput(TypedDict):
    """What the pipeline produces: analysis → summary → recommendations."""
    analysis: str
    summary: str
    recommendations: list[str]
```

## Pipeline Orchestration

```python
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver

@entrypoint(checkpointer=InMemorySaver())
def pipeline(report: PipelineInput) -> PipelineOutput:
    analysis = analyze_report(report["report_text"]).result()

    if classify_patient(analysis) == "normal":
        return PipelineOutput(analysis=analysis, summary="", recommendations=[])

    summary = generate_summary(analysis).result()
    approved = interrupt({"question": "Approve recommendations?", "analysis": analysis, "summary": summary})

    if not approved:
        return PipelineOutput(analysis=analysis, summary=summary, recommendations=[])

    recommendations = generate_recommendations(analysis, summary).result()
    return PipelineOutput(analysis=analysis, summary=summary, recommendations=recommendations)
```

### Notes

- Each `@task` call returns a future; `.result()` resolves it. Launch several
  before awaiting to run them in parallel.
- `interrupt(...)` pauses the graph until a client resumes with `Command(resume=...)`
  — the human-in-the-loop checkpoint.
- `RetryPolicy` on `@task` replaces the old manual retry loop (max 3 attempts).

## Pipeline Flow

```
START
  │
  ▼
[Agent 1: analyze_report]
  │
  ▼
[classify_patient] ──normal──▶ return early (skip summary + recommendations)
  │ abnormal
  ▼
[Agent 2: generate_summary]
  │
  ▼
[interrupt → human approves] ──rejected──▶ return early
  │ approved
  ▼
[Agent 3: generate_recommendations]
  │
  ▼
END
```

The **critical** path (classified as `critical`) routes to an alert-human alternative flow instead of the normal pipeline path.