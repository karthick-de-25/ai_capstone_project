# 03 — Implement Classifier helper with conditional routing

**Type:** task
**Status:** open

## Description

Implement the `classify_patient` helper and the routing `if/elif` logic that sits inside the entrypoint between Agent 1 and Agent 2.

## Requirements

- `classify_patient(analysis: str) -> str` returning `"normal" | "abnormal" | "critical"`
- In the `@entrypoint`, route:
  - `normal` → return early (skip summary + recommendations)
  - `critical` → send alert via `interrupt()` (alternative human-alert flow)
  - `abnormal` → proceed to Summary Agent
- Classification based on analysis content (LLM decides from the findings)

## File location

`src/pipeline/agents/analysis.py` (classifier helper lives with Agent 1)

## Dependencies

- Agent 1 output (`analysis`)
- `src/pipeline/contracts.py` — `PipelineOutput`
- `langgraph.types.interrupt` for the critical flow