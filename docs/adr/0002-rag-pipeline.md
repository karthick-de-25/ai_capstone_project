# ADR-0002: LangChain + ChromaDB for RAG Pipeline

**Status:** Accepted

**Date:** 2026-03-15

## Context

The capstone requires a RAG pipeline that retrieves relevant medical guideline context and injects it into LLM prompts. Options considered:

1. **LangChain + ChromaDB** — recommended in rubric, fast to prototype
2. **LlamaIndex** — alternative ecosystem, stronger indexing but heavier
3. **Manual retrieval** — no framework, direct embedding + cosine similarity

## Decision

Use **LangChain 1.x** for document loading, splitting, and retrieval, with **ChromaDB** as the persistent vector store.

- **Loader:** `langchain_community.document_loaders.PyPDFLoader` for medical guideline PDFs
- **Splitter:** `langchain_text_splitters.RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200)
- **Embeddings:** `langchain_openai.OpenAIEmbeddings` (model `text-embedding-3-small`)
- **Vector Store:** `langchain_chroma.Chroma` (persistent to `./chroma_db/`)
- **Composition:** LangChain 1.x LCEL style — `RunnableParallel` (retriever + question) → `ChatPromptTemplate` → `ChatOpenAI` → `StrOutputParser`
  (`langchain.chains.create_retrieval_chain` was removed in 1.x — we use LCEL directly)
- **Ensemble / multi-query retrieval (future):** `langchain_classic.retrievers.MultiQueryRetriever` / `EnsembleRetriever` (the `langchain_classic` compat package ships with `langchain-community`)
- **FAISS (alternative):** `langchain_faiss` wrapper when an in-memory vector store is preferred

## Consequences

- **Positive:** LangChain integrates directly with LangGraph (both from the same ecosystem)
- **Positive:** ChromaDB persists to disk — no re-embedding on restart
- **Positive:** Easy to swap to FAISS for performance testing
- **Positive:** Metadata filtering enables report-type-specific retrieval
- **Negative:** LangChain 1.x splits integrations into standalone packages (splitters, Chroma, community) — we import from each specific package; no `langchain[all]`
- **Negative:** `langchain-community` is in sunset mode (0.4.x, no 1.x) — `PyPDFLoader`/`BM25Retriever` still work today; long-term migration target is standalone packages
- **Mitigation:** Import only what's needed per package; keep RAG imports isolated in the RAG module so they are swappable

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| LlamaIndex | More complex; steeper learning curve; overkill for our retrieval scope |
| Manual retrieval | Would need to implement chunking, embedding, store, and search ourselves — no benefit |
| FAISS only | Good for in-memory, but ChromaDB gives persistence at minimal extra cost |