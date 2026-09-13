# 02 — Implement Report Analysis Agent node

**Type:** task
**Status:** open

## Description

Implement the `analyze_report` LangGraph node function. This is Agent 1 in the pipeline.

## Requirements

- Function signature: `analyze_report(state: ClinicalState) -> dict`
- Calls ChatOpenAI with the report analysis system prompt
- Returns `{"analysis": str}` on success
- Returns `{"analysis": str, "errors": list}` on failure
- Error handling for LLM timeouts and API errors

## File location

`src/pipeline/agents/report_analysis.py`

## Dependencies

- `src/pipeline/state.py` — ClinicalState schema
- `src/data/synthetic/report_generator.py` — for testing