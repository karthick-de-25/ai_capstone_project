# 03 — Implement Classifier node with conditional routing

**Type:** task
**Status:** open

## Description

Implement the `classify_report` node and the `route_after_classification` edge function. These sit between Agent 1 and Agent 2.

## Requirements

- `classify_report(state) -> {"classification": "normal"|"abnormal"|"critical"}`
- `route_after_classification(state) -> Literal["summarize", "alert_human", "__end__"]`
- Classification based on analysis content (LLM decides from the findings)
- Critical route → alternative alert-human path (separate from main summary path)

## File location

`src/pipeline/agents/classifier.py`

## Dependencies

- Agent 1 output (`state.analysis`)
- `src/pipeline/state.py` — ClinicalState