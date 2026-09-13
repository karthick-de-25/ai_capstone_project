# Feature: Summary Agent

## Description

The Summary Agent is Agent 2 in the 3-agent pipeline. It takes the structured analysis output from Agent 1 and produces a concise, bullet-point clinical summary.

## Input

```python
"analysis": "Key Findings:\n- Elevated fasting glucose (180 mg/dL, normal: 70-110)\n..."
```

## Output (appended to state)

```python
"summary": "**Key Findings:**\n- ⚠️ Fasting glucose: **180 mg/dL** (high)\n..."
```

## Acceptance Criteria

1. **Conciseness** — Summary is 3-5 bullet points, no longer than ~500 chars
2. **Completeness** — All abnormal values from the analysis appear in the summary
3. **Emphasis** — Abnormal values are visually marked (──ing or ⚠️ prefix)
4. **No hallucination** — Summary contains no information not present in the analysis
5. **Empty state** — If analysis says "no abnormal findings," summary outputs "No abnormal findings detected."
6. **Graceful degradation** — LLM failure returns a fallback message

## Dependencies

- Agent 1 output (`state.analysis`)
- LLM: OpenAI GPT-4o-mini

## Owner

Raj

## Status

`open`