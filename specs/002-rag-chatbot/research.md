# Research: RAG Chatbot for Physical AI & Humanoid Robotics Book

**Branch**: `002-rag-chatbot` | **Date**: 2025-12-13 | **Spec**: [spec.md](./spec.md)

## Phase 0 Research Summary

This document captures research findings for all technical unknowns identified in the planning phase.

---

## R1: Python 3.13 Compatibility with LangChain

**Decision**: Use Python 3.13 with LangChain 0.3.x

**Rationale**:
- Python 3.13 is the latest stable release (October 2024)
- LangChain 0.3.x (released late 2024) has full Python 3.13 support
- Performance improvements in Python 3.13's JIT compiler benefit LLM workloads
- Constitution v1.1.0 mandates Python 3.13

**Alternatives Considered**:
- Python 3.11/3.12: More established but Constitution requires 3.13
- Python 3.10: Wider library support but outdated

**Windows-Specific Notes**:
- Python 3.13 Windows installer available from python.org
- Use `py -3.13` launcher or add to PATH
- Virtual environments: `python -m venv venv`

---

## R2: LangChain RAG Pipeline Architecture

**Decision**: Use LangChain's LCEL (LangChain Expression Language) for RAG pipeline

**Rationale**:
- LCEL provides declarative, composable pipeline definitions
- Native streaming support for real-time responses
- Built-in retry logic and fallback handling
- Clean separation between retrieval and generation

**Components Selected**:
- `langchain-core`: Base abstractions
- `langchain-openai` or `langchain-community`: LLM provider integration
- `langchain-qdrant`: Native Qdrant vector store integration
- `langchain-text-splitters`: Document chunking

**Alternatives Considered**:
- LlamaIndex: More opinionated, less flexibility for custom pipelines
- Raw OpenAI API: No built-in RAG abstractions, more boilerplate
- Haystack: Heavier, enterprise-focused

---

## R3: Embedding Model Selection

**Decision**: Use OpenAI `text-embedding-3-small` (1536 dimensions)

**Rationale**:
- Best price/performance ratio for semantic search
- 1536 dimensions provide good accuracy
- Well-supported by LangChain
- Alternative: `text-embedding-3-large` (3072 dims) for higher accuracy at 2x cost

**Local Alternative** (if no API key):
- `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
- Free, runs locally, lower accuracy

**Alternatives Considered**:
- Cohere embeddings: Good but separate API key management
- Google's embedding models: Less LangChain integration
- BGE embeddings: Good local option but requires more setup

---

## R4: Qdrant Deployment Strategy

**Decision**: Docker for local development, Qdrant Cloud optional for production

**Rationale**:
- Docker provides consistent local environment
- Single `docker run` command to start
- Qdrant Cloud free tier offers 1GB storage (sufficient for book content)
- Constitution mandates Qdrant as vector storage

**Docker Command**:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

**Collection Configuration**:
- Distance metric: Cosine similarity
- Vector size: 1536 (matching embedding model)
- Payload indexing for metadata filters

---

## R5: FastAPI + Uvicorn Configuration

**Decision**: FastAPI with Uvicorn ASGI server, async endpoints

**Rationale**:
- Constitution mandates FastAPI + Uvicorn
- Async support critical for non-blocking LLM calls
- Automatic OpenAPI documentation
- Pydantic v2 for request/response validation

**Configuration Decisions**:
- Single worker for local development
- Streaming responses via `StreamingResponse`
- CORS middleware for frontend integration
- Health check endpoint at `/health`

---

## R6: Document Chunking Strategy

**Decision**: RecursiveCharacterTextSplitter with 400 token chunks, 50 token overlap

**Rationale**:
- 400 tokens provides sufficient context per chunk
- 50 token overlap prevents context loss at boundaries
- RecursiveCharacterTextSplitter respects paragraph/sentence boundaries
- Spec requires 300-500 tokens (FR-007)

**Chunk Metadata**:
- `source`: File path relative to docs folder
- `title`: Document title from frontmatter or filename
- `section`: Heading hierarchy (H1 > H2 > H3)
- `chunk_index`: Position within document

---

## R7: LLM Selection for Response Generation

**Decision**: Support multiple providers via environment variable

**Rationale**:
- User may have different API keys available
- LangChain supports provider switching
- Default to OpenAI GPT-4o-mini for cost efficiency

**Supported Providers**:
1. OpenAI (GPT-4o-mini, GPT-4o)
2. Anthropic (Claude 3 Haiku, Claude 3.5 Sonnet)
3. Google (Gemini 1.5 Flash, Gemini 1.5 Pro)

**Configuration**:
```
LLM_PROVIDER=openai  # or anthropic, google
LLM_MODEL=gpt-4o-mini
```

---

## R8: Citation Generation Strategy

**Decision**: Include source metadata in prompt context, enforce citation in system prompt

**Rationale**:
- FR-004 requires citations in every response
- Constitution Principle V mandates passage-level citations
- System prompt instructs LLM to cite sources by reference number

**Implementation**:
- Each retrieved chunk includes `[Source N]` marker
- System prompt: "Always cite sources using [Source N] format"
- Response includes source list at end

---

## R9: Error Handling and Fallback

**Decision**: Graceful degradation with user-friendly messages

**Rationale**:
- FR-005 requires "not found" message
- FR-011 requires graceful error handling
- Constitution Principle V requires informative feedback

**Error Categories**:
| Error Type | User Message |
|------------|--------------|
| No relevant chunks | "I couldn't find relevant information in the book for your question." |
| LLM timeout | "Response is taking longer than expected. Please try again." |
| Qdrant unavailable | "The search service is temporarily unavailable. Please try again later." |
| Invalid query | "Please provide a question about the book content." |

---

## R10: Windows Development Environment

**Decision**: PowerShell-based setup with explicit Windows compatibility

**Rationale**:
- Constitution requires error-free installation on Windows
- Python 3.13 Windows installer from python.org
- Docker Desktop for Qdrant
- `.env` file for configuration

**Setup Requirements**:
1. Python 3.13 from python.org
2. Docker Desktop with WSL 2 backend
3. Git for Windows
4. Visual Studio Code (recommended)

---

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| Which embedding model? | OpenAI text-embedding-3-small |
| Local or cloud Qdrant? | Docker local, Cloud optional |
| Chunk size? | 400 tokens with 50 overlap |
| Which LLM? | Configurable, default GPT-4o-mini |
| Session storage? | In-memory for MVP (no Postgres needed) |

---

## Next Steps

1. Proceed to Phase 1: Design & Contracts
2. Generate data-model.md with entity definitions
3. Create OpenAPI contract in contracts/
4. Write quickstart.md with step-by-step setup
