# AI Clinical Report Summarization Assistant — Context

## Project

A multi-agent system that helps doctors quickly understand clinical reports by automatically analyzing, summarizing, and generating follow-up recommendations. Built as a Healthcare domain capstone using LangGraph + LangChain.

## Glossary

| Term | Definition |
|------|------------|
| **Clinical Report** | A medical document containing patient information, lab results, assessments, and physician notes. Input to the pipeline. |
| **Report Analysis Agent** | Agent 1. Ingests a raw clinical report and extracts key findings, abnormal values, and notable observations. |
| **Summary Agent** | Agent 2. Takes the analysis output and produces a concise, structured clinical summary. |
| **Recommendation Agent** | Agent 3. Generates actionable follow-up recommendations based on the analysis and summary. |
| **Pipeline** | The directed graph of agents executing sequentially: Analysis → Summary → Recommendation. |
| **Human-in-the-Loop (HITL)** | A checkpoint that pauses pipeline execution for a human clinician to review and approve before recommendations are generated. |
| **Classification** | The severity label assigned after analysis: `normal`, `abnormal`, or `critical`. Controls conditional routing. |
| **RAG Pipeline** | Retrieval-Augmented Generation — retrieves relevant medical guideline chunks from a vector store and injects them into the LLM prompt for context. |
| **Thread** | A LangGraph thread identified by `thread_id`. Each patient conversation gets its own thread for state persistence and memory. |
| **Vector Store** | ChromaDB (persistent) or FAISS (in-memory) that stores embeddings of medical guideline PDFs for RAG retrieval. |
| **Synthetic Data** | Realistic-but-fabricated patient reports, lab test PDFs, and medical guidelines generated for development. No real patient data is used. |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        PIPELINE                          │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │  Report   │───▶│  Summary  │───▶│  Recommendation   │  │
│  │ Analysis  │    │  Agent    │    │     Agent         │  │
│  │  Agent    │    │           │    │                   │  │
│  └────┬─────┘    └─────┬─────┘    └────────┬──────────┘  │
│       │                │                    │             │
│       ▼                ▼                    ▼             │
│  Classification    Human Approval        Output:         │
│  [normal/abnormal/  Checkpoint         3-5 Follow-up     │
│   critical]         (interrupt)        Recommendations   │
│                                                          │
│  Conditional Routing:                                    │
│    normal   → END (skip summary)                         │
│    abnormal → Summary Agent                               │
│    critical → Alert Human (alternative flow)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     RAG PIPELINE                         │
│                                                          │
│  Medical Guideline PDFs                                  │
│        │                                                 │
│        ▼                                                 │
│  PyPDFLoader → Text Splitter → Embeddings → ChromaDB     │
│                                              │           │
│  User Query ──▶ Retriever ──▶ LLM ──▶ Answer            │
│                    ▲                                      │
│              Relevant chunks                              │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Agent Framework | LangGraph | StateGraph with checkpoints, interrupts for HITL, conditional edges |
| LLM | OpenAI GPT-4o-mini | Cost-effective for capstone; swap to Gemini via `langchain-google-genai` |
| RAG | LangChain | Document loaders, splitters, retrieval chains |
| Vector DB | ChromaDB | Persistent, simple setup, metadata filtering |
| Embeddings | OpenAI `text-embedding-3-small` | 1536-dim, good retrieval quality |

## Key Architectural Decisions

See `docs/adr/` for full rationale:

1. **[ADR-0001](docs/adr/0001-agent-architecture.md)**: Sequential 3-agent pipeline with conditional routing — simple, testable, matches capstone rubric.
2. **[ADR-0002](docs/adr/0002-rag-pipeline.md)**: LangChain + ChromaDB for RAG — recommended in rubric, fast to prototype.
3. **[ADR-0003](docs/adr/0003-human-in-the-loop.md)**: LangGraph `interrupt`/`Command` for HITL — native to LangGraph, no custom state machine needed.

## File Layout

```
/
├── CONTEXT.md              ← You are here
├── agent.md                ← Agent specifications and prompts
├── requirements.txt        ← Python dependencies
├── guidelines.md           ← Program-level capstone guidelines
├── todo.md                 ← Team task tracking
├── docs/
│   ├── workflow.md         ← Orchestration and routing details
│   └── adr/               ← Architecture Decision Records
├── .scratch/               ← Issue tracker (feature specs & tickets)
│   ├── feature-report-analysis/
│   ├── feature-summary-agent/
│   └── feature-recommendation-agent/
├── .pi/                    ← Pi coding-agent config + skills
│   ├── settings.json
│   └── skills/
│       ├── langchain/     ← LangChain skill (RAG patterns)
│       ├── langgraph/     ← LangGraph skill (agent orchestration)
│       ├── feature-plan/
│       └── feature-implement/
└── src/                    ← (to be created) Application code
```

## Design Constraints

- **No real patient data.** All data is synthetic, generated by the team.
- **Local-only.** No cloud deployment required. ChromaDB persists locally.
- **Sequential-first.** The core pipeline is sequential; conditional routing adds branching.
- **One mandatory HITL checkpoint.** Before generating recommendations.
- **Error resilience.** Each node catches failures; pipeline retries up to 3 times before falling back.