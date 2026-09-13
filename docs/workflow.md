# Workflow Orchestration

## Pipeline Topology

The AI Clinical Report Summarization Assistant uses a **sequential pipeline with conditional branching** built on LangGraph's `StateGraph`.

### Core Flow

```
START ──▶ Report Analysis ──▶ Classifier ──▶ Summary ──▶ HITL Check ──▶ Recommendations ──▶ END
```

### Conditional Branches

| Condition | Route | Rationale |
|-----------|-------|-----------|
| `classification == "normal"` | END | No abnormalities to summarize or recommend on |
| `classification == "abnormal"` | Summary Agent | Standard path |
| `classification == "critical"` | Alert Human (separate flow) | Requires immediate clinician attention |
| Human rejects recommendations | END | Clinician disagrees — stop |
| Agent failure (retries exhausted) | Fallback END | Graceful degradation |

## Graph Definition (LangGraph)

```python
from langgraph.graph import StateGraph, START, END
from typing import Literal

builder = StateGraph(ClinicalState)

# Nodes
builder.add_node("analyze",     analyze_report)
builder.add_node("classify",    classify_report)
builder.add_node("summarize",   generate_summary)
builder.add_node("human_review", human_checkpoint)
builder.add_node("recommend",   generate_recommendations)
builder.add_node("alert_human", alert_human_node)

# Edges
builder.add_edge(START, "analyze")
builder.add_edge("analyze", "classify")

# Conditional: after classification
builder.add_conditional_edges(
    "classify",
    route_after_classification,
    {
        "summarize":   "summarize",
        "alert_human": "alert_human",
        END:           END,
    },
)

# Human alert path
builder.add_edge("alert_human", END)

# Main path
builder.add_edge("summarize", "human_review")

# Conditional: after human review
builder.add_conditional_edges(
    "human_review",
    route_after_human_review,
    {
        "recommend": "recommend",
        END:         END,
    },
)

builder.add_edge("recommend", END)
```

## Routing Functions

```python
def route_after_classification(
    state: ClinicalState,
) -> Literal["summarize", "alert_human", "__end__"]:
    """Route based on severity classification."""
    c = state.get("classification", "abnormal")
    if c == "normal":
        return "__end__"
    elif c == "critical":
        return "alert_human"
    else:
        return "summarize"

def route_after_human_review(
    state: ClinicalState,
) -> Literal["recommend", "__end__"]:
    """Route based on human approval."""
    if state.get("human_approved", False):
        return "recommend"
    return "__end__"
```

## Human-in-the-Loop Checkpoint

Implemented via LangGraph's `interrupt` + `Command`:

1. Pipeline executes through `summarize` node
2. `human_checkpoint` node fires `interrupt(...)`, pausing execution
3. User reviews analysis + summary and decides
4. Pipeline resumes via `Command(resume={"approved": True/False})`

```python
def human_checkpoint(state: ClinicalState) -> dict:
    response = interrupt({
        "question": "Approve recommendations?",
        "analysis": state["analysis"],
        "summary": state["summary"],
    })
    approved = response.get("approved", False)
    return {"human_approved": approved, "requires_human_review": True}
```

## Parallel Execution (Future Enhancement)

The pipeline is **sequential** by design (each agent depends on the previous output). However, there is an opportunity for parallel execution inside the RAG retrieval layer:

```
User Query
    │
    ├──▶ ChromaDB Retriever (dense)
    ├──▶ BM25 Retriever (sparse)
    └──▶ LLM Re-ranker
    │
    └──▶ Ensemble Fusion ▶▶ LLM Response
```

This uses LangChain's `EnsembleRetriever` for hybrid search.

## Error Handling & Retries

```
Agent Node
    │
    ├── success ▶ next node
    │
    └── failure (error appended to state.errors)
        │
        ├── retry_count < 3 ▶ retry node
        └── retry_count >= 3 ▶ fallback output + END
```

## Logging & Monitoring

Every node logs via Python's `logging` module:

```python
import logging
log = logging.getLogger(__name__)

def analyze_report(state):
    log.info("Agent 1: Analyzing report...")
    # ... work ...
    log.info(f"Analysis complete. {len(state['analysis'])} chars")
```

Logged events:
- Node entry/exit
- Classification result
- Human checkpoint triggered
- Errors and retries
- Pipeline completion