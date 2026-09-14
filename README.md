# AI Clinical Report Summarization Assistant

> **Healthcare Domain Capstone** — Enterprise Capstone: AI Agents & Workflows

A multi-agent AI system that assists doctors by automatically **analyzing**, **summarizing**, and generating **follow-up recommendations** from clinical reports — reducing the time doctors spend reading lengthy reports so patient care decisions aren't delayed.

## 🏥 Problem

Doctors spend excessive time reading long clinical reports, delaying patient care decisions. This system automates the first-pass reading with a 3-agent pipeline.

## ✅ Implemented Features

### 🧠 Full 3-Agent Pipeline (LangGraph 1.x)

| # | Agent | File | Owner |
|---|-------|------|-------|
| 1 | [Report Analysis Agent](agent.md#agent-1-report-analysis-agent) | `src/pipeline/agents/analysis.py` | Karthick |
| 2 | [Summary Agent](agent.md#agent-2-summary-agent) | `src/pipeline/agents/summary.py` | Raj |
| 3 | [Recommendation Agent](agent.md#agent-3-recommendation-agent) | `src/pipeline/agents/recommendation.py` | Mahesh |

### Pipeline Orchestration (`src/pipeline/pipeline.py`)

```
Report ──▶ Analysis Agent ──▶ Classifier ──▶ Summary Agent ──▶ Human Review ──▶ Recommendations
                ▲                                       │
                └── critical ──▶ Alert Human ────────────┘
```

- **Sequential execution** — Analysis → Summary → Recommendation
- **Conditional routing** — `normal` (early exit) / `abnormal` (standard path) / `critical` (alert-human flow)
- **Human-in-the-loop** — Two `interrupt()` checkpoints: critical alert bypass, and recommendation approval gate
- **Cross-report memory** — Passing `previous_summary` allows the Summary Agent to include a "Trend vs Previous" section

### 🧪 LLM Factory (`src/pipeline/llm.py`)
- One shared `ChatOpenAI` instance, configurable via `OPENROUTER_API_KEY` or `OPENAI_API_KEY`
- `inject_llm(fake_llm)` / `reset_llm()` for fully offline unit testing (no API key required)

### 🏗️ Clinical Calculation Tools (`src/pipeline/tools/clinical.py`)
- BMI calculation + WHO classification
- eGFR (MDRD formula) + CKD staging
- Blood pressure classification (AHA/ACC stages)
- Embedded in Agent 1 via `_compute_tools_from_report()` — report text is scanned for weight, height, creatinine, and BP, and computed metrics are injected into the LLM prompt

### 📄 Synthetic Report Generator (`src/data/synthetic/report_generator.py`)
- `generate_report(variant="normal|abnormal|critical", seed=N)`
- Realistic patient demographics, lab values (glucose, HbA1c, LDL, HDL, creatinine), vitals, and assessments
- Deterministic output per seed for reproducible tests

### 🖥️ CLI Entry Point (`src/main.py`)
- `python src/main.py` — Runs sample report or reads from `--report <file>`
- Multi-report memory chaining loop: after each run, prompts for another report (same patient) to demonstrate cross-report trend tracking
- Handles both `interrupt()` checkpoints (critical alert + approval gate)

### 🧪 Test Suite (21+ tests, no API key needed)

| File | Coverage |
|------|----------|
| `tests/test_pipeline.py` | Normal/abnormal/critical paths, rejection, memory chain, contract validation |
| `tests/test_synthetic.py` | Report generation for all 3 variants, determinism, file output, edge cases |
| `tests/test_tools.py` | BMI, eGFR, BP classification, report parsing all 6 functions |

All tests use `FakeListChatModel` from `langchain_core` — run with `pytest -q` without any API key.

## 🤖 Agents

| # | Agent | Role | Owner |
|---|-------|------|-------|
| 1 | [Report Analysis Agent](agent.md#agent-1-report-analysis-agent) | Extracts key findings, abnormal values, impressions | Karthick |
| 2 | [Summary Agent](agent.md#agent-2-summary-agent) | Produces concise clinical summary | Raj |
| 3 | [Recommendation Agent](agent.md#agent-3-recommendation-agent) | Generates follow-up recommendations | Mahesh |

## 🧰 Tech Stack

| Layer | Tool |
|-------|------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) 1.x (`@entrypoint`/`@task`) |
| RAG | [LangChain](https://github.com/langchain-ai/langchain) 1.x (LCEL) — design complete, not yet wired |
| LLM | OpenRouter (default) / OpenAI GPT-4o-mini |
| Vector DB | ChromaDB (persistent) / FAISS (in-memory) — planned for RAG step |
| Embeddings | OpenAI `text-embedding-3-small` — planned for RAG step |

## 📁 Repository Structure

```
/
├── CONTEXT.md                        ← Domain glossary + architecture overview
├── agent.md                          ← Agent specs, prompts, contracts
├── guidelines.md                     ← Capstone program reference guide
├── requirements.txt                  ← Python dependencies
├── todo.md                           ← Team task tracking
├── docs/
│   ├── workflow.md                   ← Orchestration & routing details
│   └── adr/                          ← Architecture Decision Records
│       ├── 0001-agent-architecture.md
│       ├── 0002-rag-pipeline.md
│       └── 0003-human-in-the-loop.md
├── .scratch/                         ← Issue tracker (per issue-tracker.md)
│   ├── feature-pipeline-baseline/
│   ├── feature-report-analysis/
│   ├── feature-summary-agent/
│   └── feature-recommendation-agent/
├── .pi/                              ← Pi agent config + skills
│   └── skills/
│       ├── langchain/                ← LangChain skill (RAG patterns)
│       └── langgraph/                ← LangGraph skill (orchestration)
├── src/                              ← Application code (fully implemented)
│   ├── main.py                       ← CLI entry point
│   ├── pipeline/
│   │   ├── contracts.py              ← PipelineInput / PipelineOutput TypedDicts
│   │   ├── llm.py                    ← LLM factory (+ test injection)
│   │   ├── pipeline.py               ← @entrypoint orchestrator
│   │   ├── agents/
│   │   │   ├── analysis.py           ← Agent 1 + classifier
│   │   │   ├── summary.py            ← Agent 2
│   │   │   └── recommendation.py     ← Agent 3
│   │   └── tools/
│   │       └── clinical.py           ← BMI, eGFR, BP tools
│   └── data/synthetic/
│       └── report_generator.py       ← Synthetic report generator
└── tests/
    ├── test_pipeline.py              ← Pipeline integration tests
    ├── test_synthetic.py             ← Synthetic data tests
    └── test_tools.py                 ← Clinical tools tests
```

## 📥 Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key in `.env`:
```bash
# .env — either OpenRouter or OpenAI
OPENROUTER_API_KEY=sk-or-v1-...
# or
OPENAI_API_KEY=sk-...
```

## 🚀 Usage

```bash
# Run with the built-in sample report (hardcoded abnormal case)
python src/main.py

# Run with a report from a text file
python src/main.py --report path/to/report.txt

# Single run (no multi-report memory loop)
python src/main.py --no-loop
```

The pipeline will:
1. Analyze the report and classify severity
2. (for abnormal/critical) Generate a structured summary
3. Pause for **human approval** before recommendations
4. (if approved) Generate 3–5 actionable follow-up recommendations

For critical reports, an **immediate alert** interrupts the pipeline before summary generation.

### Tests (no API key required)

```bash
pytest -q tests/
```

## 🚀 Roadmap

### ✅ Completed

- [x] Project setup + documentation (CONTEXT.md, agent.md, ADRs, workflow docs)
- [x] Synthetic clinical report data generator
- [x] **Report Analysis Agent** — extraction + classification + clinical tools
- [x] **Summary Agent** — structured bullet-point summaries with cross-report memory
- [x] **Recommendation Agent** — 3–5 actionable follow-ups
- [x] **LangGraph pipeline** — sequential orchestration, conditional routing, HITL interrupts
- [x] **CLI entry point** — multi-report memory chaining loop
- [x] **Full test suite** — 21+ tests using fake LLM (no API key needed)

### ⏳ Pending / Next

| Priority | Task | Details |
|----------|------|--------|
| 🔴 High | **RAG Pipeline** | Ingest medical guideline PDFs → ChromaDB → retrieval chain grounded in Agent 3. ADR-0002 design is complete, code is not yet written. |
| 🟡 Medium | **Update `.scratch/` issue statuses** | All 5 issue files still show `Status: open` despite code being implemented — need to close them. |
| 🟡 Medium | **Error handling enhancements** | RetryPolicy is wired on all @tasks; add broader fallback patterns and user-facing error messages. |
| 🟡 Medium | **Logging / monitoring** | Basic Python logging exists; add configurable log levels, structured JSON output, or dashboard hooks. |
| 🟢 Low | **Demo script + presentation** | End-to-end demo script and capstone presentation materials. |

See [todo.md](todo.md) and `.scratch/` for detailed tracking.

## 📈 Evaluation Criteria Coverage

| Criteria | Coverage | Max |
|----------|----------|-----|
| Architecture clarity & documentation | ✅ Documented in CONTEXT.md, agent.md, ADRs, workflow.md | 5/25 |
| Working implementation / functional demo | ✅ 3 agents + pipeline + CLI + tests | 10/25 |
| RAG quality and relevance | ❓ Design complete (ADR-0002), code pending | 5/25 |
| System design coherence | ✅ Coherent architecture with clear contracts | 5/25 |
| Proper agent role separation | ✅ Each agent is a separate @task with distinct role | 5/20 |
| Prompt engineering quality | ✅ Clinical domain prompts with structured output | 5/20 |
| Memory and context handling | ✅ Cross-report memory via previous_summary | 5/20 |
| Human-in-the-loop implementation | ✅ Two interrupt() checkpoints (critical + approval) | 5/20 |
| Sequential workflow | ✅ Sequential Analysis → Summary → Recommendation | 5/15 |
| Parallel / router workflow | ✅ Conditional routing (normal/abnormal/critical) | 5/15 |
| Tool usage and orchestration | ✅ Clinical tools (BMI, eGFR, BP) injected into Agent 1 | 5/15 |
| Error handling and graceful failures | ✅ RetryPolicy on all tasks | 5/15 |
| Logging and monitoring | ✅ Basic logging; structured monitoring is pending | 5/15 |
| Workflow reliability | ✅ Tested with fake LLM + HITL resume flows | 5/15 |
| Demo quality | ⏳ CLI works; presentation pending | 5/25 |
| Architecture explanation | ✅ Complete write-up | 5/25 |
| Team participation | ✅ Roles assigned per agent | 5/25 |

## 🛡️ Responsible AI

- **Synthetic data only** — No real patient data is ever used
- **Human approval gating** — Recommendations require clinician sign-off
- **Explainable outputs** — Summaries cite the specific abnormal findings they're based on
- **Graceful failure** — Errors never silently produce clinical advice

## 📚 Documentation Index

| Doc | Purpose |
|-----|---------|
| [CONTEXT.md](CONTEXT.md) | Domain glossary, vocabulary, architecture |
| [agent.md](agent.md) | Agent definitions, prompts, I/O contracts |
| [docs/workflow.md](docs/workflow.md) | Orchestration, routing, HITL, retries |
| [docs/adr/0001](docs/adr/0001-agent-architecture.md) | Agent topology decision |
| [docs/adr/0002](docs/adr/0002-rag-pipeline.md) | RAG stack decision |
| [docs/adr/0003](docs/adr/0003-human-in-the-loop.md) | HITL mechanism decision |
| [docs/agents/domain.md](docs/agents/domain.md) | How to read domain docs |
| [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md) | Issue tracker conventions |