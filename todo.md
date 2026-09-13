# AI Clinical Report Summarization Assistant — Tasks

## Project Setup ✅
- [x] Create CONTEXT.md — domain glossary + architecture overview
- [x] Create agent.md — agent specifications + prompts + contracts
- [x] Create docs/workflow.md — orchestration + routing + HITL
- [x] Create docs/adr/0001-agent-architecture.md — sequential + conditional topology
- [x] Create docs/adr/0002-rag-pipeline.md — LangChain + ChromaDB
- [x] Create docs/adr/0003-human-in-the-loop.md — LangGraph interrupt/Command
- [x] Create requirements.txt — pinned dependencies
- [x] Install LangChain + LangGraph pi skills

## Features (In Progress)

### Feature 1: Report Analysis Agent — Karthick
- [ ] `.scratch/feature-report-analysis/spec.md` — spec defined
- [ ] Synthetic clinical report data generation
- [ ] Report Analysis agent implementation
- [ ] Tests: parsing, error handling, classification

### Feature 2: Summary Agent — Raj
- [ ] `.scratch/feature-summary-agent/spec.md` — spec defined
- [ ] Summary agent implementation
- [ ] Tests: formatting, edge cases, fallback

### Feature 3: Recommendation Agent — Mahesh
- [ ] `.scratch/feature-recommendation-agent/spec.md` — spec defined
- [ ] Recommendation agent implementation
- [ ] Tests: count, quality, error handling

### Integration
- [ ] Connect 3 agents into LangGraph pipeline
- [ ] Human-in-the-loop checkpoint
- [ ] RAG pipeline with medical guideline PDFs
- [ ] Error handling + retries
- [ ] Logging + monitoring
- [ ] End-to-end demo script
- [ ] Presentation materials

## Evaluation Criteria
- [ ] Architecture clarity and documentation (5/25)
- [ ] Working implementation / functional demo (10/25)
- [ ] RAG quality and relevance (5/25)
- [ ] System design coherence (5/25)
- [ ] Proper agent role separation (5/20)
- [ ] Prompt engineering quality (5/20)
- [ ] Memory and context handling (5/20)
- [ ] Human-in-the-loop implementation (5/20)
- [ ] Sequential workflow (5/15)
- [ ] Parallel / router workflow (5/15)
- [ ] Tool usage and orchestration (5/15)
- [ ] Error handling and graceful failures (5/15)
- [ ] Logging and monitoring (5/15)
- [ ] Workflow reliability (5/15)
- [ ] Demo quality (5/25)
- [ ] Architecture explanation (5/25)
- [ ] Team participation (5/25)