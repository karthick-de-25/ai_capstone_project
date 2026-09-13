# Feature Plan & Progress Log — Project Baseline (LangGraph)

> **Effort:** feature-pipeline-baseline
> **Goal:** Runnable 3-agent sequential `@entrypoint`/`@task` skeleton with `src/` package layout.
> **Stack (validated):** LangGraph `1.2.11` (latest stable) + LangChain 1.x (`langchain-core>=1.4.7,<2`)
> **Checked-in:** 2026 · session record

---

## Status Summary

| Step | Name | Status | Notes |
|------|------|--------|-------|
| 1 | Scaffold & Contracts | ✅ **DONE** | `src/` package, `contracts.py`, `requirements.txt` pinned to 1.x |
| 2 | Core Logic (happy path) | ⏳ **NEXT** | 3 `@task` agents + `@entrypoint` pipeline |
| 3 | Entry Point & Tests | ⏳ pending | CLI + fake-LLM test |
| — | Docs sync to LangGraph 1.x | ✅ **DONE** | All `.md` + skills updated & verified |

---

## Decisions (locked)

| # | Decision | Detail |
|---|----------|--------|
| D1 | **LangGraph 1.2.11 (latest stable)** | Decorator API `@entrypoint` / `@task`. Replaces legacy `StateGraph`/`add_node`/`add_edge` (0.2–0.3.x). |
| D2 | **LangChain 1.x pinned** | `langchain-core>=1.4.7,<2.0`; splitters in `langchain_text_splitters`; `langchain.chains` removed → LCEL composition. |
| D3 | **Contract file is `src/pipeline/contracts.py`** | `PipelineInput` (`report_text`) + `PipelineOutput` (`analysis`, `summary`, `recommendations`). No mutable shared-state dict (1.x data flows via task args/returns). |
| D4 | **HITL via `interrupt()` + `Command(resume=...)`** | Requires `checkpointer=InMemorySaver()` on `@entrypoint` (from `langgraph.checkpoint.memory`, ships in `langgraph-checkpoint`). |
| D5 | **Retries via `RetryPolicy`** | `@task(retry_policy=RetryPolicy(max_attempts=3))` — replaces manual retry loop. |
| D6 | **Routing = plain Python** | `classify_patient(analysis)` helper + `if/elif` inside entrypoint. No router nodes/edges. |
| D7 | **`langgraph-checkpoint` is a separate package** | Needed for `InMemorySaver`. SQLite/Postgres savers are separate packages (`langgraph-checkpoint-sqlite` / `-postgres`) — not in scope. |
| D8 | **`langchain-community` is sunset** (0.4.2, no 1.x) | Still used for `PyPDFLoader`/`BM25Retriever` in RAG step; migration target = standalone packages. `langchain-faiss` 0.1.x is an empty stub — NOT usable. |

---

## Verified API Facts (tested against langgraph 1.2.11)

1. `@entrypoint` takes **one input parameter** — pass a dict/TypedDict for multiple fields; it is **NOT unpacked by key**.
2. Each `@task` call returns a future; `.result()` resolves it. Launch several, then await → parallel (measured: 3×0.2s tasks ≈ 0.21s).
3. Run config: `{"configurable": {"thread_id": "..."}}`.
4. `interrupt(value)` raises `GraphInterrupt` on first call; resume with `command(resume=...)`.
5. Interrupt payload surfaced in `.stream(...)` as `{'__interrupt__': (Interrupt(value=..., id=...),)}`.
6. On resume, completed `@task` results are **cached by the checkpointer — not re-run**.
7. `RetryPolicy` fields: `max_attempts` (default 3), `initial_interval`, `backoff_factor`, `max_interval`, `jitter`, `retry_on`.
8. `langgraph.__version__` does **NOT** exist in 1.x — use `importlib.metadata.version("langgraph")`.
9. Tools: `langgraph.prebuilt.create_react_agent` (verified importable).

---

## Step 1 — Scaffold & Contracts ✅

### Files created
| File | Status | Content |
|------|--------|---------|
| `src/__init__.py` | new, 0 lines | package marker |
| `src/pipeline/__init__.py` | new, 0 lines | subpackage marker |
| `src/pipeline/contracts.py` | new, +27 | `PipelineInput` / `PipelineOutput` TypedDicts |
| `requirements.txt` | M, +20/-14 | pinned 1.x stack |

### Verification
- ✅ `contracts.py` imports cleanly (pure TypedDict, no deps needed):
  - `PipelineInput` fields: `['report_text']`
  - `PipelineOutput` fields: `['analysis', 'summary', 'recommendations']`
- ✅ `pip -r requirements.txt` resolves in scratch venv:
  `langgraph 1.2.11 · langgraph-checkpoint 4.2.0 · langchain-core 1.6.3 · langchain-openai 1.6.2`

---

## Docs Sync to LangGraph 1.x ✅

All repo docs updated to the validated 1.x contract (after user picked latest stable):

| File | What changed |
|------|--------------|
| `agent.md` | Overview, task signatures (`@task(retry_policy=...)`), contracts schema, entrypoint orchestration, pipeline flow |
| `docs/workflow.md` | Full rewrite: entrypoint definition, HITL stream/interrupt/resume, parallel fan-out, RetryPolicy |
| `docs/adr/0001` | Routing via plain-Python, fan-out instead of `Send` |
| `docs/adr/0002` | LangChain 1.x RAG: LCEL composition, `langchain_text_splitters`, community-sunset notes |
| `docs/adr/0003` | `InMemorySaver` + verified interrupt/Command code sketch |
| `CONTEXT.md` | Glossary (Pipeline def), tech stack row, file layout |
| `README.md` | Tech stack version notes |
| `.scratch/*` | 5 tickets + 1 spec → `@task` signatures, `contracts.py`, classifier-helper pattern |
| `.pi/skills/langgraph/*` | SKILL.md + pipeline-template.md → 1.x; setup.sh fixed (`importlib.metadata` instead of broken `langgraph.__version__`) |
| `.pi/skills/langchain/*` | SKILL.md → LCEL / `langchain_text_splitters` / `langchain_classic.retrievers`; faiss note; setup.sh fixed |

### Verified patterns (ran against installed 1.2.11)
- ✅ Sequential 3-node `@task`/`@entrypoint` pipeline → correct output
- ✅ `interrupt` + `Command(resume={'approved': True})` → resumed result correct; retry count == 2
- ✅ `RetryPolicy` catches transient errors
- ✅ All LangChain 1.x imports resolve (`langchain_chroma`, `langchain_text_splitters`, `langchain_classic.retrievers.multi_query` / `.ensemble`, `langchain_community.retrievers.BM25Retriever`)

---

## Step 2 — Core Logic (happy path) ⏳ NEXT

- **Goal:** three `@task` nodes (analyze → summary → recommend) + `@entrypoint` pipeline + `get_llm()` factory (swappable fake/real).
- **Files (planned):**
  - `src/pipeline/agents/__init__.py`
  - `src/pipeline/agents/analysis.py` — `analyze_report` + `classify_patient`
  - `src/pipeline/agents/summary.py` — `generate_summary`
  - `src/pipeline/agents/recommendation.py` — `generate_recommendations`
  - `src/pipeline/pipeline.py` — `@entrypoint pipeline(report: PipelineInput) -> PipelineOutput`
  - `src/pipeline/llm.py` — `get_llm()` factory (+ fake injection point for tests)
- **~150 lines target.**
- **Risks:** LLM calls need `OPENAI_API_KEY` in `main`, but tests must run keyless via fake LLM.

## Step 3 — Entry Point & Tests ⏳

- **Files (planned):**
  - `src/main.py` — CLI, sample report, prints pipeline output; handles interrupt with `Command(resume=...)`
  - `tests/test_pipeline.py` — runs graph with `FakeListChatModel` (from `langchain_core.language_models.fake_chat_models`), asserts state fields
- **Accept:** `pytest -q` green without API key; `python src/main.py` works with `OPENAI_API_KEY`.

---

## Out of Scope (tracked in `.scratch/` separately)

- Synthetic data generator → `.scratch/feature-report-analysis/issues/01`
- Classifier conditional routing → `issues/03`
- Human-in-the-loop interrupt wiring → ADR-0003, workflow.md (documented; wired in Step 2/3)
- RAG/ChromaDB → ADR-0002, RAG step

## Resumption Notes

If this session is interrupted: Step 1 + docs sync are committed as described above.
Next action = **Step 2 Core Logic** — present files/risks, wait for approval, then implement
(`@task` agents + `@entrypoint` + fake-LLM testability via `get_llm()`), per `/skill:feature-implement`.