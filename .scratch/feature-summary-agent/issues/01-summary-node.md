# 01 — Implement Summary Agent node

**Type:** task
**Status:** open

## Description

Implement the `generate_summary` LangGraph node function. This is Agent 2 in the pipeline.

## Requirements

- Function signature: `generate_summary(state: ClinicalState) -> dict`
- Calls ChatOpenAI with the summary system prompt
- Returns `{"summary": str}` — 3-5 bullet points, abnormal values marked
- Returns fallback on error

## File location

`src/pipeline/agents/summary.py`

## Acceptance

```python
result = generate_summary({"analysis": "Key Findings:\n- Glucose: 180 mg/dL (high)"})
assert "⚠️" in result["summary"] or "**" in result["summary"]
```