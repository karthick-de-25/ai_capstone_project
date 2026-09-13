# Agents — AI Clinical Report Summarization Assistant

## Overview

Three agents execute sequentially in a LangGraph StateGraph pipeline. Each agent has a distinct role, system prompt, input/output contract, and error behavior.

---

## Agent 1: Report Analysis Agent

**Role:** Extract key findings, abnormal lab values, and notable observations from a raw clinical report.

**Owner:** Karthick

### Input

| Field | Type | Description |
|-------|------|-------------|
| `report_text` | `string` | Raw clinical report text (lab results, physician notes, patient info) |

### Output (appended to state)

| Field | Type | Description |
|-------|------|-------------|
| `analysis` | `string` | Structured analysis: key findings, abnormal values, impressions |
| `classification` | `string` | Severity label: `normal`, `abnormal`, or `critical` (set by classifier node) |

### System Prompt

```
You are a clinical report analyst. Extract key findings, abnormal lab values,
and notable observations from this report. Be thorough but concise.

Report:
{report_text}
```

### Error Handling

- Catches LLM failures → returns `"Analysis unavailable due to error."`
- Appends error to `state.errors[]`
- Retry node loops up to 3 times on failure

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

### Output (appended to state)

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

### Error Handling

- Catches LLM failures → returns `"Summary unavailable due to error."`
- Appends error to `state.errors[]`

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

### Output (appended to state)

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

### Error Handling

- Catches LLM failures → returns `["Unable to generate recommendations due to an error."]`
- Appends error to `state.errors[]`

### Tests

- ✅ Generates 3-5 recommendations for a diabetes + hypertension case
- ✅ Handles empty analysis + summary → generic fallback recommendation
- ✅ Handles LLM failure → fallback list

---

## Agent State Schema (LangGraph)

```python
from typing import TypedDict, Annotated
import operator

class ClinicalState(TypedDict):
    # Input
    report_text: str

    # Agent outputs (populated sequentially)
    analysis: str
    classification: str          # normal | abnormal | critical
    summary: str
    recommendations: list[str]

    # Human-in-the-loop
    requires_human_review: bool
    human_approved: bool

    # Error handling
    retry_count: int
    errors: Annotated[list[str], operator.add]   # Accumulates across nodes
```

## Pipeline Flow

```
START
  │
  ▼
[Agent 1: Report Analysis]
  │
  ▼
[Classifier Node] ──normal──▶ END
  │                          (skip summary + recommendations)
  │ abnormal
  ▼
[Agent 2: Summary]
  │
  ▼
[Human Checkpoint] ──rejected──▶ END
  │ approved
  ▼
[Agent 3: Recommendation]
  │
  ▼
  END
```

The **critical** path (classified as `critical`) routes to an alert-human alternative flow instead of the normal pipeline path.