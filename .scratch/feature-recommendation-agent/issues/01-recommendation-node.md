# 01 — Implement Recommendation Agent node

**Type:** task
**Status:** open

## Description

Implement the `generate_recommendations` LangGraph node function. This is Agent 3 in the pipeline.

## Requirements

- Function signature: `generate_recommendations(state: ClinicalState) -> dict`
- Only called after human approval (`state.human_approved == True`)
- Calls ChatOpenAI with the recommendation system prompt
- Parses LLM output into `list[str]` (3-5 items)
- Returns `{"recommendations": list[str]}`
- Returns fallback list on error

## File location

`src/pipeline/agents/recommendation.py`

## Acceptance

```python
result = generate_recommendations({"analysis": "High glucose", "summary": "⚠️ Glucose high"})
assert 3 <= len(result["recommendations"]) <= 5
```