# Feature: Recommendation Agent

## Description

The Recommendation Agent is Agent 3 in the 3-agent pipeline. It generates 3-5 actionable follow-up recommendations based on the analysis and summary. This agent only runs after human approval.

## Input

```python
"analysis": "Key Findings:\n- Elevated fasting glucose (180 mg/dL)...",
"summary": "**Key Findings:**\n- ⚠️ Fasting glucose: **180 mg/dL**..."
```

## Output (appended to state)

```python
"recommendations": [
    "Schedule follow-up HbA1c test in 3 months.",
    "Consider adjusting Metformin dosage — current 1000mg BID may need increase.",
    "Refer to endocrinologist for uncontrolled diabetes management."
]
```

## Acceptance Criteria

1. **Count** — Always returns 3-5 recommendations (list of strings)
2. **Actionability** — Each recommendation is a specific action, not general advice
3. **Faithfulness** — Recommendations are based only on analysis + summary content
4. **Format** — Clean list of strings, no markdown formatting on individual items
5. **Empty state** — If analysis and summary are empty/unavailable, returns a single generic fallback
6. **Graceful degradation** — LLM failure returns `["Unable to generate recommendations"]`

## Dependencies

- Agent 1 output (`state.analysis`)
- Agent 2 output (`state.summary`)
- `human_approved == True` (this agent is gated by HITL checkpoint)
- LLM: OpenAI GPT-4o-mini

## Owner

Mahesh

## Status

`open`