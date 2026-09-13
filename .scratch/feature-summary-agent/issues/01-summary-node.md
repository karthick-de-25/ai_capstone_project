# 01 — Implement Summary Agent node

**Type:** task
**Status:** open

## Description

Implement the `generate_summary` LangGraph 1.x `@task` function. This is Agent 2 in the pipeline.

## Requirements

- Function signature: `@task(retry_policy=RetryPolicy(max_attempts=3)) def generate_summary(analysis: str) -> str`
- Calls ChatOpenAI with the summary system prompt
- Returns `str` — 3-5 bullet points, abnormal values marked
- Raises on failure — `RetryPolicy` retries transient errors

## File location

`src/pipeline/agents/summary.py`

## Acceptance

```python
result = generate_summary("Key Findings:\n- Glucose: 180 mg/dL (high)")
assert "⚠️" in result or "**" in result
```