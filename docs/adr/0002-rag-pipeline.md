# ADR-0002: LangChain + ChromaDB for RAG Pipeline

**Status:** Accepted

**Date:** 2026-03-15

## Context

The capstone requires a RAG pipeline that retrieves relevant medical guideline context and injects it into LLM prompts. Options considered:

1. **LangChain + ChromaDB** — recommended in rubric, fast to prototype
2. **LlamaIndex** — alternative ecosystem, stronger indexing but heavier
3. **Manual retrieval** — no framework, direct embedding + cosine similarity

## Decision

Use **LangChain** for document loading, splitting, and retrieval, with **ChromaDB** as the persistent vector store.

- **Loader:** `PyPDFLoader` for medical guideline PDFs
- **Splitter:** `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200)
- **Embeddings:** `OpenAIEmbeddings` (model `text-embedding-3-small`)
- **Vector Store:** `Chroma` (persistent to `./chroma_db/`)
- **Retrieval:** `create_retrieval_chain` with `create_stuff_documents_chain` for simple Q&A
- **Ensemble:** `EnsembleRetriever` with BM25 for hybrid search (future enhancement)

## Consequences

- **Positive:** LangChain integrates directly with LangGraph (both from the same ecosystem)
- **Positive:** ChromaDB persists to disk — no re-embedding on restart
- **Positive:** Easy to swap to FAISS for performance testing
- **Positive:** Metadata filtering enables report-type-specific retrieval
- **Negative:** LangChain ecosystem is large; we only use a subset (loaders, splits, retriever, chains)
- **Mitigation:** Import only what's needed; no `langchain[all]` dependency

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| LlamaIndex | More complex; steeper learning curve; overkill for our retrieval scope |
| Manual retrieval | Would need to implement chunking, embedding, store, and search ourselves — no benefit |
| FAISS only | Good for in-memory, but ChromaDB gives persistence at minimal extra cost |