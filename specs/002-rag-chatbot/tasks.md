# Tasks: RAG Chatbot for Physical AI & Humanoid Robotics Book

**Input**: Design documents from `/specs/002-rag-chatbot/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/openapi.yaml
**Constitution**: v1.1.0 (Python 3.13, FastAPI, Uvicorn, LangChain, Qdrant)

**Tests**: Not explicitly requested in spec - test tasks omitted per template guidelines.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Backend**: `backend/` at repository root
- **API Routes**: `backend/api/routes/`
- **Services**: `backend/services/`
- **Core**: `backend/core/`
- **Scripts**: `backend/scripts/`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project structure, dependencies, and configuration files

- [ ] T001 Create backend directory structure per plan.md: `backend/`, `backend/api/`, `backend/api/routes/`, `backend/api/models/`, `backend/services/`, `backend/core/`, `backend/scripts/`
- [ ] T002 [P] Create `backend/requirements.txt` with Python 3.13 compatible dependencies: fastapi>=0.115.0, uvicorn[standard]>=0.32.0, pydantic>=2.9.0, python-dotenv>=1.0.0, langchain>=0.3.0, langchain-core>=0.3.0, langchain-openai>=0.2.0, langchain-qdrant>=0.2.0, langchain-text-splitters>=0.3.0, qdrant-client>=1.12.0, httpx>=0.27.0, tiktoken>=0.8.0
- [ ] T003 [P] Create `backend/.env.example` with placeholders: OPENAI_API_KEY, LLM_PROVIDER, LLM_MODEL, EMBEDDING_MODEL, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, DOCS_PATH, HOST, PORT, DEBUG
- [ ] T004 [P] Create `env.example` at project root copying backend/.env.example template
- [ ] T005 Verify Python 3.13 installation and create virtual environment in `backend/venv/`

**Verification**: Run `pip install -r requirements.txt` with no errors (Constitution Principle VIII)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create `backend/config.py` to load environment variables using python-dotenv with validation
- [ ] T007 [P] Create `backend/api/__init__.py` empty init file
- [ ] T008 [P] Create `backend/api/routes/__init__.py` empty init file
- [ ] T009 [P] Create `backend/api/models/__init__.py` empty init file
- [ ] T010 [P] Create `backend/services/__init__.py` empty init file
- [ ] T011 [P] Create `backend/core/__init__.py` empty init file
- [ ] T012 [P] Create `backend/scripts/__init__.py` empty init file
- [ ] T013 Define Pydantic schemas in `backend/api/models/schemas.py`: ChatRequest, ChatResponse, Citation, ChatStreamChunk, IngestRequest, IngestResponse, IngestStatusResponse, HealthResponse, ServiceStatus, ErrorResponse (per contracts/openapi.yaml)
- [ ] T014 Implement Qdrant client connection and collection initialization in `backend/core/qdrant_client.py` with health check method
- [ ] T015 Implement LLM client abstraction in `backend/core/llm_client.py` supporting OpenAI (default), with provider switching via env var
- [ ] T016 Create `backend/main.py` with FastAPI app initialization, CORS middleware, exception handlers, and router mounting
- [ ] T017 Verify Qdrant Docker container runs: `docker run -p 6333:6333 qdrant/qdrant`

**Checkpoint**: Foundation ready - Run `uvicorn main:app` with no errors (Constitution Principle VIII)

---

## Phase 3: User Story 2 - Ingest Book Content (Priority: P1) 🎯 MVP Prerequisite

**Goal**: As a system administrator, I want to ingest the book's Markdown/MDX content into the vector database, so that the chatbot can retrieve relevant passages for answering user queries.

**Independent Test**:
1. Run ingestion script against `/docs` folder
2. Verify chunks stored in Qdrant with `GET http://localhost:6333/collections/physical_ai_book`
3. Confirm points_count > 0

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement embedding generation using LangChain OpenAI embeddings in `backend/services/embedding_service.py`
- [ ] T019 [P] [US2] Implement document loading and MDX/MD parsing in `backend/services/ingestion_service.py`
- [ ] T020 [US2] Implement text chunking with RecursiveCharacterTextSplitter (400 tokens, 50 overlap) in `backend/services/ingestion_service.py`
- [ ] T021 [US2] Implement batch embedding and Qdrant upsert with metadata payload in `backend/services/ingestion_service.py`
- [ ] T022 [US2] Implement `POST /ingest` endpoint in `backend/api/routes/ingest.py` calling ingestion_service
- [ ] T023 [US2] Implement `GET /ingest/status` endpoint in `backend/api/routes/ingest.py` returning collection stats
- [ ] T024 [US2] Register ingest router in `backend/main.py`
- [ ] T025 [US2] Create CLI ingestion script in `backend/scripts/ingest.py` for standalone execution
- [ ] T026 [US2] Run ingestion against book content in `physical-ai-humanoid-robotics/docs/` and verify success

**Checkpoint**: User Story 2 complete - Qdrant contains embedded book chunks, `GET /ingest/status` returns total_chunks > 0

---

## Phase 4: User Story 1 - Ask Book Content Questions (Priority: P1) 🎯 MVP Core

**Goal**: As a reader, I want to ask questions about the book's content and receive accurate answers with citations, so that I can quickly find information without manually searching.

**Independent Test**:
1. POST `/chat` with query "What is ROS 2?"
2. Verify response contains answer text derived from book content
3. Verify response contains citations array with source file paths
4. POST `/chat` with out-of-scope query "What is the recipe for chocolate cake?"
5. Verify response contains "not found" message

### Implementation for User Story 1

- [ ] T027 [P] [US1] Implement vector similarity search in `backend/services/retrieval_service.py` using Qdrant client
- [ ] T028 [P] [US1] Implement LLM response generation with system prompt in `backend/services/generation_service.py`
- [ ] T029 [US1] Implement RAG pipeline orchestrating embed→retrieve→generate in `backend/services/rag_service.py`
- [ ] T030 [US1] Add citation extraction from retrieved chunks in `backend/services/rag_service.py`
- [ ] T031 [US1] Add "not found" fallback when no relevant chunks retrieved (score threshold) in `backend/services/rag_service.py`
- [ ] T032 [US1] Implement `POST /chat` endpoint in `backend/api/routes/chat.py` calling rag_service
- [ ] T033 [US1] Implement `POST /chat/stream` SSE endpoint in `backend/api/routes/chat.py` for streaming responses
- [ ] T034 [US1] Register chat router in `backend/main.py`
- [ ] T035 [US1] Add query validation (empty, too long, special chars only) in `backend/api/routes/chat.py`
- [ ] T036 [US1] Add logging for queries and responses in `backend/services/rag_service.py` (FR-012)

**Checkpoint**: User Story 1 complete - `/chat` returns accurate answers with citations, out-of-scope queries handled

---

## Phase 5: User Story 3 - Health Check and Service Status (Priority: P2)

**Goal**: As a system administrator, I want to check the health status of the chatbot service, so that I can verify all components are operational.

**Independent Test**:
1. GET `/health` when all services up → status: "healthy"
2. Stop Qdrant container, GET `/health` → status: "degraded", qdrant.status: "down"

### Implementation for User Story 3

- [ ] T037 [US3] Implement health check for Qdrant in `backend/core/qdrant_client.py` (ping collection)
- [ ] T038 [US3] Implement health check for LLM in `backend/core/llm_client.py` (test API key validity)
- [ ] T039 [US3] Implement `GET /health` endpoint in `backend/api/routes/health.py` aggregating service statuses
- [ ] T040 [US3] Register health router in `backend/main.py`
- [ ] T041 [US3] Add latency measurement to each service health check

**Checkpoint**: User Story 3 complete - `/health` accurately reflects system component status

---

## Phase 6: User Story 4 - Multi-Turn Conversation Context (Priority: P3)

**Goal**: As a reader, I want the chatbot to remember context from previous questions in the same session.

**Independent Test**:
1. POST `/chat` with query "What is ROS 2?" (include session_id in response)
2. POST `/chat` with query "What are its main components?" using same session_id
3. Verify response understands "its" refers to ROS 2

### Implementation for User Story 4

- [ ] T042 [US4] Add in-memory session storage in `backend/services/session_service.py` (dict: session_id → messages)
- [ ] T043 [US4] Modify rag_service to accept session_id and include conversation history in prompt
- [ ] T044 [US4] Update `/chat` endpoint to handle session_id parameter and return session_id
- [ ] T045 [US4] Add session cleanup for stale sessions (>30 min inactive)

**Checkpoint**: User Story 4 complete - Follow-up questions maintain context within session

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, documentation, and deployment readiness

- [ ] T046 [P] Add comprehensive error handling with ErrorResponse schema in all routes
- [ ] T047 [P] Ensure no credentials exposed in responses or logs (FR-014)
- [ ] T048 [P] Add request/response logging middleware in `backend/main.py`
- [ ] T049 Run quickstart.md validation steps end-to-end
- [ ] T050 Verify all Constitution Principle VIII checkpoints pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 2 (Phase 3)**: Depends on Foundational - MUST complete before US1 (provides content)
- **User Story 1 (Phase 4)**: Depends on US2 completion (needs ingested content to query)
- **User Story 3 (Phase 5)**: Depends on Foundational only - can run parallel to US1/US2
- **User Story 4 (Phase 6)**: Depends on US1 completion (extends chat functionality)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational
    ↓
    ├──→ Phase 3: US2 (Ingest) ──→ Phase 4: US1 (Chat) ──→ Phase 6: US4 (Sessions)
    │                                                            ↓
    └──→ Phase 5: US3 (Health) ─────────────────────────────────→ Phase 7: Polish
```

### Within Each Phase

- Tasks marked [P] can run in parallel
- Services before endpoints
- Endpoints before router registration
- Verification steps after implementation

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
# Parallel tasks:
T002 (requirements.txt)
T003 (.env.example)
T004 (env.example root)
```

**Phase 2 (Foundational)**:
```bash
# Parallel tasks:
T007, T008, T009, T010, T011, T012 (init files)
```

**Phase 3 (US2 - Ingest)**:
```bash
# Parallel tasks:
T018 (embedding_service.py)
T019 (document loading)
```

**Phase 4 (US1 - Chat)**:
```bash
# Parallel tasks:
T027 (retrieval_service.py)
T028 (generation_service.py)
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 2 (Ingest) - **VERIFY**: Content in Qdrant
4. Complete Phase 4: User Story 1 (Chat) - **VERIFY**: Queries return answers
5. **STOP and VALIDATE**: Test full RAG flow
6. Deploy MVP if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US2 (Ingest) → Content searchable
3. Add US1 (Chat) → **MVP Complete!** Users can ask questions
4. Add US3 (Health) → Operations monitoring
5. Add US4 (Sessions) → Enhanced UX
6. Polish → Production ready

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 50 |
| **Setup Tasks (Phase 1)** | 5 |
| **Foundational Tasks (Phase 2)** | 12 |
| **User Story 2 Tasks (Phase 3)** | 9 |
| **User Story 1 Tasks (Phase 4)** | 10 |
| **User Story 3 Tasks (Phase 5)** | 5 |
| **User Story 4 Tasks (Phase 6)** | 4 |
| **Polish Tasks (Phase 7)** | 5 |
| **Parallel Opportunities** | 23 tasks marked [P] |
| **MVP Scope** | Phases 1-4 (36 tasks) |

---

## Constitution Compliance

| Principle | Task(s) |
|-----------|---------|
| I. Accurate Book Content Retrieval | T029, T031 |
| II. Context-Aware Response Generation | T029, T043 |
| III. RAG Architecture with Vector Storage | T018-T021, T027 |
| IV. Modular Backend Architecture | T001, T006-T016 |
| V. Passage-Level Citation | T030 |
| VI. Dependency and Environment Integrity | T002, T005 |
| VII. Step-by-Step Implementation Discipline | All phases sequential |
| VIII. Verification and Error-Free Execution | Checkpoints after each phase |
| IX. Reliable Query Resolution Guarantee | T031, T035, T046 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US#] label maps task to specific user story for traceability
- Verify backend API via FastAPI docs at `http://localhost:8000/docs`
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Environment variables MUST be set before running backend
- Constitution Principle VIII: Verify each step passes before proceeding
