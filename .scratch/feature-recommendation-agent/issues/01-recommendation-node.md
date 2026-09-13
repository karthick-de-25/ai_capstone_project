# 01 — Implement Recommendation Agent node

**Type:** task
**Status:** open

## Description

Implement the `generate_recommendations` LangGraph 1.x `@task` function. This is Agent 3 in the pipeline.

## Requirements

- Function signature: `@task(retry_policy=RetryPolicy(max_attempts=3)) def generate_recommendations(analysis: str, summary: str) -> list[str]`
- Only called after human approval (the entrypoint gates this behind `interrupt(...)`)
- Calls ChatOpenAI with the recommendation system prompt
- Parses LLM output into `list[str]` (3-5 items)
- Returns the list on success; raises on failure

## File location

`src/pipeline/agents/recommendation.py`

## Acceptance

```python
result = generate_recommendations("High glucose", "⚠️ Glucose high")
assert 3 <= len(result) <= 5
```