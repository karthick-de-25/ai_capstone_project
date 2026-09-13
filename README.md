# AI Clinical Report Summarization Assistant

> **Healthcare Domain Capstone** — Enterprise Capstone: AI Agents & Workflows

A multi-agent AI system that assists doctors by automatically **analyzing**, **summarizing**, and generating **follow-up recommendations** from clinical reports — reducing the time doctors spend reading lengthy reports so patient care decisions aren't delayed.

## 🏥 Problem

Doctors spend excessive time reading long clinical reports, delaying patient care decisions. This system automates the first-pass reading with a 3-agent pipeline.

## 🤖 Agents

| # | Agent | Role | Owner |
|---|-------|------|-------|
| 1 | [Report Analysis Agent](agent.md#agent-1-report-analysis-agent) | Extracts key findings, abnormal values, impressions | Karthick |
| 2 | [Summary Agent](agent.md#agent-2-summary-agent) | Produces concise clinical summary | Raj |
| 3 | [Recommendation Agent](agent.md#agent-3-recommendation-agent) | Generates follow-up recommendations | Mahesh |

### Pipeline

```
Report ──▶ Analysis Agent ──▶ Classifier ──▶ Summary Agent ──▶ Human Review ──▶ Recommendations
                ▲                                       │
                └── critical ──▶ Alert Human ────────────┘
```

- **Sequential execution** — Analysis → Summary → Recommendation
- **Conditional routing** — normal/abnormal/critical classification
- **Human-in-the-loop** — clinician approves before recommendations are generated
- **RAG** — medical guideline PDFs retrieved via ChromaDB to ground LLM responses

## 🧰 Tech Stack

| Layer | Tool |
|-------|------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) 1.x (`@entrypoint`/`@task`) |
| RAG | [LangChain](https://github.com/langchain-ai/langchain) 1.x (LCEL) |
| LLM | OpenAI GPT-4o-mini |
| Vector DB | ChromaDB (persistent) / FAISS (in-memory) |
| Embeddings | OpenAI `text-embedding-3-small` |

## 📁 Repository Structure

```
/
├── CONTEXT.md                    ← Domain glossary + architecture overview
├── agent.md                      ← Agent specs, prompts, contracts
├── guidelines.md                 ← Capstone program reference guide
├── requirements.txt              ← Python dependencies
├── todo.md                       ← Team task tracking
├── docs/
│   ├── workflow.md               ← Orchestration & routing details
│   └── adr/                      ← Architecture Decision Records
│       ├── 0001-agent-architecture.md
│       ├── 0002-rag-pipeline.md
│       └── 0003-human-in-the-loop.md
├── .scratch/                     ← Issue tracker (per issue-tracker.md)
│   ├── feature-report-analysis/
│   ├── feature-summary-agent/
│   └── feature-recommendation-agent/
├── .pi/                          ← Pi agent config + skills
│   └── skills/
│       ├── langchain/            ← LangChain skill
│       └── langgraph/            ← LangGraph skill
└── src/                          ← (to be built) application code
```

## 📥 Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key:
```bash
export OPENAI_API_KEY=sk-...
```

## 🚀 Roadmap

- [x] Project setup + documentation (CONTEXT.md, agent.md, workflows, ADRs)
- [ ] **Report Analysis Agent** — synthetic data, extraction, classification (Karthick)
- [ ] **Summary Agent** — structured concise summaries (Raj)
- [ ] **Recommendation Agent** — 3-5 follow-ups (Mahesh)
- [ ] Integration — LangGraph pipeline, HITL checkpoint, RAG, error handling
- [ ] Demo + presentation

See [todo.md](todo.md) and `.scratch/` for detailed tracking.

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