# Feature: Report Analysis Agent

## Description

The Report Analysis Agent is Agent 1 in the 3-agent pipeline. It ingests a raw clinical report (text, not PDF — PDF parsing is handled upstream by the document loader) and extracts:

- Key findings and observations
- Abnormal lab values with normal range comparison
- Notable clinical impressions
- A severity classification (`normal` / `abnormal` / `critical`)

The output feeds into the Classifier node which routes the pipeline.

## Input

```python
"report_text": "Patient: John Doe, M/45\nLab Results:\n- Glucose: 180 mg/dL..."
```

## Output (appended to state)

```python
"analysis": "Key Findings:\n- Elevated fasting glucose (180 mg/dL, normal: 70-110)\n...",
"classification": "abnormal",   # set by classifier node after analysis
```

## Acceptance Criteria

1. **Extraction accuracy** — Given a synthetic clinical report, the agent extracts all key findings, abnormal values, and impressions.
2. **Classification correctness** — Given a report with:
   - All values in range → classifies as `normal`
   - At least one value out of range → classifies as `abnormal`
   - Life-threatening values (e.g., glucose > 300, BP > 180/120) → classifies as `critical`
3. **Graceful degradation** — If the LLM call fails (timeout, auth error), returns error message and appends to `state.errors`
4. **Empty input handling** — Empty string input returns a clear "no report" message
5. **Consistent format** — Analysis output follows a consistent structured format (Key Findings → Abnormal Values → Impressions)

## Dependencies

- `src/data/synthetic/` — synthetic report data generator (to be created)
- `src/pipeline/contracts.py` — `PipelineInput`/`PipelineOutput` TypedDicts (created)
- LLM: OpenAI GPT-4o-mini

## Implementation Notes (LangGraph 1.x)

- Agent 1 is a `@task` function: `@task(retry_policy=RetryPolicy(max_attempts=3)) def analyze_report(report_text: str) -> str`
- No separate classifier node — `classify_patient(analysis)` is a plain helper called from the `@entrypoint`

## Owner

Karthick

## Status

`open`