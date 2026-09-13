# 02 — Implement Report Analysis Agent node

**Type:** task
**Status:** open

## Description

Implement the `analyze_report` LangGraph 1.x `@task` function. This is Agent 1 in the pipeline.

## Requirements

- Function signature: `@task(retry_policy=RetryPolicy(max_attempts=3)) def analyze_report(report_text: str) -> str`
- Calls ChatOpenAI with the report analysis system prompt
- Returns `str` (the analysis) on success
- Raises on failure — `RetryPolicy` retries transient errors (max 3 attempts)
- Error handling for LLM timeouts and API errors

## File location

`src/pipeline/agents/analysis.py`

## Dependencies

- `src/pipeline/contracts.py` — `PipelineInput`/`PipelineOutput` TypedDicts
- `src/data/synthetic/report_generator.py` — for testing