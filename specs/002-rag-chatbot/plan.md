# Implementation Plan: RAG Chatbot for Physical AI & Humanoid Robotics Book

**Branch**: `002-rag-chatbot` | **Date**: 2025-12-13 | **Spec**: [spec.md](./spec.md)
**Constitution**: v1.1.0 | **Status**: Ready for Implementation

---

## Summary

Build a production-ready RAG (Retrieval-Augmented Generation) chatbot that answers questions from the "Physical AI & Humanoid Robotics" book. The system uses Python 3.13, FastAPI with Uvicorn, LangChain for RAG orchestration, and Qdrant for vector storage. All answers are context-aware, based exclusively on book content, and include citations.

---

## Technical Context

| Aspect | Decision |
|--------|----------|
| **Language/Version** | Python 3.13 |
| **Primary Dependencies** | FastAPI, Uvicorn, LangChain, Qdrant-client |
| **Storage** | Qdrant (vector), In-memory (sessions for MVP) |
| **Testing** | pytest with pytest-asyncio |
| **Target Platform** | Windows (development), Linux (production) |
| **Project Type** | Backend API service |
| **Performance Goals** | <5s response time for 95% of queries |
| **Constraints** | Local Qdrant (Docker) or Qdrant Cloud Free Tier |
| **Scale/Scope** | ~50-100 book documents, ~1000 chunks |

---

## Constitution Check

*GATE: All principles verified before implementation.*

| Principle | Status | Implementation |
|-----------|--------|----------------|
| I. Accurate Book Content Retrieval | ✅ | RAG ensures answers from book only |
| II. Context-Aware Response Generation | ✅ | LangChain RAG pipeline with context injection |
| III. RAG Architecture with Vector Storage | ✅ | Qdrant + LangChain integration |
| IV. Modular Backend Architecture | ✅ | FastAPI with service separation |
| V. Passage-Level Citation | ✅ | Citation object in every response |
| VI. Dependency and Environment Integrity | ✅ | Python 3.13, verified requirements.txt |
| VII. Step-by-Step Implementation Discipline | ✅ | Sequential tasks in tasks.md |
| VIII. Verification and Error-Free Execution | ✅ | Health checks, verification steps |
| IX. Reliable Query Resolution Guarantee | ✅ | 90% accuracy target, error handling |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-rag-chatbot/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Setup guide
├── contracts/
│   └── openapi.yaml     # API contract
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2: Implementation tasks
```

### Source Code (repository root)

```text
backend/
├── main.py                    # FastAPI application entry
├── config.py                  # Environment configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not committed)
├── .env.example               # Environment template
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat endpoints (/chat, /chat/stream)
│   │   ├── ingest.py          # Ingestion endpoints
│   │   └── health.py          # Health check endpoint
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Pydantic request/response models
│
├── services/
│   ├── __init__.py
│   ├── rag_service.py         # RAG pipeline orchestration
│   ├── embedding_service.py   # Embedding generation
│   ├── retrieval_service.py   # Vector search
│   ├── generation_service.py  # LLM response generation
│   └── ingestion_service.py   # Document processing
│
├── core/
│   ├── __init__.py
│   ├── qdrant_client.py       # Qdrant connection management
│   └── llm_client.py          # LLM provider abstraction
│
└── scripts/
    ├── __init__.py
    └── ingest.py              # CLI ingestion script

tests/
├── __init__.py
├── conftest.py                # Pytest fixtures
├── test_health.py             # Health endpoint tests
├── test_chat.py               # Chat endpoint tests
├── test_ingest.py             # Ingestion tests
└── test_rag_service.py        # RAG pipeline unit tests
```

**Structure Decision**: Backend-only architecture (no frontend in scope). Single `backend/` directory with modular service separation per Constitution Principle IV.

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (HTTP)                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (main.py)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ /health     │  │ /chat       │  │ /ingest     │                  │
│  │ health.py   │  │ chat.py     │  │ ingest.py   │                  │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘                  │
└──────────────────────────┼────────────────┼─────────────────────────┘
                           │                │
                           ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVICES LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     rag_service.py                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │
│  │  │ embedding   │─▶│ retrieval   │─▶│ generation_service  │   │   │
│  │  │ _service    │  │ _service    │  │ (LLM + Citations)   │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   ingestion_service.py                        │   │
│  │  Load MDX ─▶ Chunk ─▶ Embed ─▶ Store in Qdrant               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                           │                │
                           ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CORE LAYER                                  │
│  ┌─────────────────────┐        ┌─────────────────────┐             │
│  │   qdrant_client.py  │        │   llm_client.py     │             │
│  │   (Qdrant Cloud or  │        │   (OpenAI/Anthropic │             │
│  │    Local Docker)    │        │    via LangChain)   │             │
│  └──────────┬──────────┘        └──────────┬──────────┘             │
└─────────────┼───────────────────────────────┼───────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────┐           ┌─────────────────────┐
│   Qdrant Vector DB  │           │    LLM Provider     │
│   (localhost:6333   │           │    (OpenAI API)     │
│    or Cloud)        │           │                     │
└─────────────────────┘           └─────────────────────┘
```

### Data Flow: Query Processing

```
1. User Query: "What is ROS 2?"
         │
         ▼
2. POST /chat { query: "What is ROS 2?" }
         │
         ▼
3. rag_service.process_query()
         │
         ├─▶ embedding_service.embed(query)
         │         │
         │         ▼
         │   OpenAI text-embedding-3-small
         │         │
         │         ▼
         │   Vector [1536 floats]
         │
         ├─▶ retrieval_service.search(vector)
         │         │
         │         ▼
         │   Qdrant similarity search
         │         │
         │         ▼
         │   Top 5 relevant chunks + metadata
         │
         └─▶ generation_service.generate(query, chunks)
                   │
                   ▼
             Build prompt with context + chunks
                   │
                   ▼
             LLM (GPT-4o-mini) generates answer
                   │
                   ▼
             Extract citations from chunk metadata
                   │
                   ▼
4. Return ChatResponse { answer, citations, query_id }
```

### Data Flow: Ingestion

```
1. POST /ingest { docs_path: "./docs" }
         │
         ▼
2. ingestion_service.ingest_documents()
         │
         ├─▶ Scan docs_path for *.md, *.mdx files
         │
         ├─▶ For each file:
         │     │
         │     ├─▶ Load and parse content
         │     │
         │     ├─▶ Extract metadata (title, module)
         │     │
         │     ├─▶ Chunk with RecursiveCharacterTextSplitter
         │     │     (400 tokens, 50 overlap)
         │     │
         │     ├─▶ Generate embeddings for each chunk
         │     │
         │     └─▶ Upsert to Qdrant with payload
         │
         └─▶ Return IngestResponse { documents_processed, chunks_created }
```

---

## Subsystem Breakdown

### 1. Backend (FastAPI)

**Purpose**: Serve HTTP API endpoints for chat, ingestion, and health checks.

**Components**:
- `main.py`: Application factory, router mounting, CORS middleware
- `api/routes/`: Endpoint handlers
- `api/models/schemas.py`: Pydantic models for validation

**Key Decisions**:
- Async endpoints for non-blocking I/O
- Streaming support via `StreamingResponse`
- OpenAPI documentation auto-generated

### 2. Vector Database (Qdrant)

**Purpose**: Store and retrieve vector embeddings of book content.

**Configuration**:
- Collection: `physical_ai_book`
- Vector size: 1536 (OpenAI text-embedding-3-small)
- Distance: Cosine similarity
- Payload: text, source, title, section, position

**Deployment Options**:
- Local: Docker `qdrant/qdrant` on port 6333
- Cloud: Qdrant Cloud Free Tier (1GB)

### 3. Embeddings System

**Purpose**: Convert text to vector representations.

**Provider**: OpenAI `text-embedding-3-small`

**Alternative**: Local `sentence-transformers/all-MiniLM-L6-v2` (384 dims)

**Process**:
- Query embedding: Single text → single vector
- Document embedding: Batch chunks → batch vectors

### 4. Ingestion Pipeline

**Purpose**: Process book MDX files into searchable chunks.

**Steps**:
1. Discover: Glob `*.md` and `*.mdx` in docs folder
2. Parse: Extract frontmatter, content, headings
3. Chunk: RecursiveCharacterTextSplitter (400 tokens, 50 overlap)
4. Embed: Generate vectors via embedding service
5. Store: Upsert to Qdrant with metadata payload

**Incremental Updates**:
- Hash content to detect changes
- Skip unchanged documents
- Delete removed documents

### 5. Chat Completion Pipeline

**Purpose**: Generate answers from queries using RAG.

**Steps**:
1. Embed query
2. Retrieve top-k chunks (k=5) from Qdrant
3. Build prompt with context
4. Generate response with LLM
5. Extract citations from chunk sources
6. Return structured response

**System Prompt**:
```
You are a helpful assistant for the "Physical AI & Humanoid Robotics" book.
Answer questions using ONLY the provided context from the book.
If the context doesn't contain the answer, say "I couldn't find this information in the book."
Always cite your sources using [Source N] format.
```

### 6. Deployment Path

**Local Development**:
1. Docker for Qdrant
2. Uvicorn with `--reload`
3. `.env` for configuration

**Production (Optional)**:
- Backend: Render.com or Fly.io
- Qdrant: Qdrant Cloud
- Environment: Secrets manager

---

## Dependencies & Tools

### Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115.0 | Web framework |
| uvicorn | >=0.32.0 | ASGI server |
| pydantic | >=2.9.0 | Data validation |
| python-dotenv | >=1.0.0 | Environment management |
| langchain | >=0.3.0 | RAG orchestration |
| langchain-core | >=0.3.0 | Base abstractions |
| langchain-openai | >=0.2.0 | OpenAI integration |
| langchain-qdrant | >=0.2.0 | Qdrant integration |
| langchain-text-splitters | >=0.3.0 | Document chunking |
| qdrant-client | >=1.12.0 | Vector DB client |
| httpx | >=0.27.0 | HTTP client |
| tiktoken | >=0.8.0 | Token counting |

### Development Dependencies

| Package | Purpose |
|---------|---------|
| pytest | Testing framework |
| pytest-asyncio | Async test support |
| pytest-cov | Coverage reports |
| black | Code formatting |
| ruff | Linting |

### External Services

| Service | Usage | Free Tier |
|---------|-------|-----------|
| OpenAI API | Embeddings + LLM | Pay-per-use |
| Qdrant (Docker) | Vector storage | Free (local) |
| Qdrant Cloud | Vector storage | 1GB free |

### Local Setup Requirements

- Python 3.13
- Docker Desktop (for Qdrant)
- Git
- ~500MB disk space

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Python 3.13 dependency issues** | Medium | High | Pin versions, test in venv, fallback to 3.12 |
| **Qdrant connection failures** | Low | High | Health checks, retry logic, clear error messages |
| **API key missing/invalid** | Medium | High | Startup validation, helpful error messages |
| **No relevant chunks found** | Medium | Medium | Graceful "not found" response, log for analysis |
| **LLM hallucination** | Low | High | Strict system prompt, temperature=0, citations required |
| **Large document processing** | Low | Medium | Chunking limits, progress logging, batch processing |
| **Windows path issues** | Medium | Medium | Use pathlib, test on Windows explicitly |

---

## Success Checklist

| Criterion | Test | Pass Condition |
|-----------|------|----------------|
| Dependencies install | `pip install -r requirements.txt` | No errors |
| Server starts | `uvicorn main:app` | No errors, listening on 8000 |
| Health check passes | `GET /health` | Status 200, all services "up" |
| Qdrant connected | Health check | qdrant.status = "up" |
| Ingestion works | `POST /ingest` | Documents processed > 0 |
| Query works | `POST /chat` with book question | Answer with citations |
| Out-of-scope handled | `POST /chat` with unrelated question | "Not found" message |
| Response time | Query timing | <5 seconds |
| No unhandled errors | Various queries | No 500 errors |

---

## Related Documents

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Technical research findings
- [data-model.md](./data-model.md) - Entity definitions
- [quickstart.md](./quickstart.md) - Setup guide
- [contracts/openapi.yaml](./contracts/openapi.yaml) - API contract
- [checklists/requirements.md](./checklists/requirements.md) - Quality checklist

---

## Next Steps

1. Run `/sp.tasks` to generate implementation task list
2. Follow quickstart.md for environment setup
3. Implement tasks sequentially per Constitution Principle VII
4. Verify each step per Constitution Principle VIII
