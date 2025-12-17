# Implementation Plan: Reusable Subagents for Physical AI & Humanoid Robotics

**Branch**: `003-reusable-subagents` | **Date**: 2025-12-17 | **Spec**: [spec.md](./spec.md)
**Constitution**: v2.0.0 | **Status**: Ready for Implementation

---

## Summary

Implement a modular subagent architecture using Claude Code Subagents and Agent Skills to provide domain-specific intelligence for the Physical AI & Humanoid Robotics book chatbot. The system will include four specialized subagents (Glossary, Hardware, Module Info, Capstone) with automatic query routing, enabling reusable intelligence across chapters while maintaining the existing RAG infrastructure.

---

## Technical Context

| Aspect | Decision |
|--------|----------|
| **Language/Version** | Python 3.13 |
| **Primary Dependencies** | FastAPI, LangChain, Qdrant-client, Claude Code SDK (anthropic) |
| **Storage** | Qdrant (vectors), In-memory (session context) |
| **Testing** | pytest with pytest-asyncio |
| **Target Platform** | Windows (development), Linux (production) |
| **Project Type** | Backend API service with subagent orchestration |
| **Performance Goals** | <5s response time, <2s routing decision |
| **Constraints** | Must integrate with existing RAG pipeline, agents must be independently testable |
| **Scale/Scope** | 4 initial subagents, expandable to N agents without core modifications |

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation |
|-----------|--------|----------------|
| I. Accurate Book Content Retrieval | ✅ | All subagents derive answers from RAG pipeline |
| II. Context-Aware Response Generation | ✅ | Subagents receive domain-filtered context |
| III. RAG Architecture with Vector Storage | ✅ | Extends existing Qdrant infrastructure |
| IV. Modular Backend Architecture | ✅ | Each subagent is independent module |
| V. Passage-Level Citation | ✅ | Citations preserved through delegation |
| VI. Dependency Integrity | ✅ | Minimal new dependencies (router only) |
| VII. Step-by-Step Implementation | ✅ | Sequential tasks in tasks.md |
| VIII. Verification | ✅ | Individual agent tests + integration tests |
| IX. Reliable Query Resolution | ✅ | Fallback to base agent if routing fails |
| X. Modular Subagent Architecture | ✅ | Core requirement of this feature |
| XI. Domain-Specific Agent Isolation | ✅ | Four isolated domain agents |
| XII. Seamless Query Delegation | ✅ | Query router with transparent UX |
| XIII. Agent Scalability | ✅ | Registration-based discovery |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-reusable-subagents/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Setup guide
├── contracts/
│   └── openapi.yaml     # Updated API contract with subagent endpoints
└── tasks.md             # Phase 2: Implementation tasks (via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py           # Agent exports and registry
│   │   ├── base_agent.py         # Abstract base class for all subagents
│   │   ├── book_agent.py         # Existing RAG agent (unchanged)
│   │   ├── glossary_agent.py     # Glossary term definitions
│   │   ├── hardware_agent.py     # Hardware requirements guidance
│   │   ├── module_info_agent.py  # Module-specific explanations
│   │   ├── capstone_agent.py     # Capstone project guidance
│   │   └── router.py             # Query router / orchestrator
│   │
│   ├── skills/
│   │   ├── __init__.py           # Skill exports
│   │   ├── citation_skill.py     # Shared citation formatting
│   │   ├── rag_skill.py          # Shared RAG retrieval operations
│   │   └── context_skill.py      # Session context management
│   │
│   ├── models/
│   │   └── schemas.py            # Extended with subagent schemas
│   │
│   ├── routes/
│   │   ├── chat.py               # Updated with router integration
│   │   └── agents.py             # New agent management endpoints
│   │
│   └── services/
│       └── rag_pipeline.py       # Updated to use router
│
└── tests/
    ├── agents/
    │   ├── test_glossary_agent.py
    │   ├── test_hardware_agent.py
    │   ├── test_module_info_agent.py
    │   ├── test_capstone_agent.py
    │   └── test_router.py
    └── integration/
        └── test_subagent_integration.py
```

**Structure Decision**: Extends existing `backend/app/` structure with dedicated `agents/` and `skills/` packages. Each subagent is a separate module enabling independent testing and reusability per Constitution Principles X and XI.

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
│  │ /health     │  │ /chat       │  │ /agents     │                  │
│  │ health.py   │  │ chat.py     │  │ agents.py   │                  │
│  └─────────────┘  └──────┬──────┘  └─────────────┘                  │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      QUERY ROUTER (router.py)                        │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Intent Classifier → Route Decision → Agent Selection       │   │
│   │                                                             │   │
│   │  Rules:                                                     │   │
│   │  • "What is X?" / "Define Y" → Glossary Agent              │   │
│   │  • "Hardware" / "specs" / "requirements" → Hardware Agent  │   │
│   │  • "Module X" / "explain how" → Module Info Agent          │   │
│   │  • "capstone" / "project" / "humanoid" → Capstone Agent   │   │
│   │  • Multi-domain → Coordinate multiple agents               │   │
│   │  • Unknown → Fallback to Book Agent                        │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Glossary   │   │  Hardware   │   │ Module Info │   │  Capstone   │
│   Agent     │   │   Agent     │   │   Agent     │   │   Agent     │
│             │   │             │   │             │   │             │
│ ─────────── │   │ ─────────── │   │ ─────────── │   │ ─────────── │
│ Domain:     │   │ Domain:     │   │ Domain:     │   │ Domain:     │
│ Technical   │   │ Workstation │   │ ROS 2       │   │ Autonomous  │
│ Terms       │   │ Jetson      │   │ Gazebo      │   │ Humanoid    │
│ ROS 2       │   │ Sensors     │   │ Isaac       │   │ Pipeline    │
│ Gazebo      │   │ GPUs        │   │ VLA         │   │ Integration │
│ Isaac       │   │             │   │ Concepts    │   │ Milestones  │
│ VLA         │   │             │   │             │   │             │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │                 │
       └─────────────────┴────────┬────────┴─────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SHARED SKILLS LAYER                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  Citation Skill │  │    RAG Skill    │  │  Context Skill  │      │
│  │  ────────────── │  │  ───────────── │  │  ───────────── │      │
│  │  Format refs    │  │  Domain filter │  │  Session mgmt  │      │
│  │  Extract sources│  │  Vector search │  │  History       │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CORE LAYER                                  │
│  ┌─────────────────────┐        ┌─────────────────────┐             │
│  │   qdrant_service.py │        │   embedding_service │             │
│  └──────────┬──────────┘        └──────────┬──────────┘             │
└─────────────┼───────────────────────────────┼───────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────┐           ┌─────────────────────┐
│   Qdrant Vector DB  │           │    LLM Provider     │
│   (book embeddings) │           │    (OpenAI/Gemini)  │
└─────────────────────┘           └─────────────────────┘
```

### Data Flow: Query with Subagent Routing

```
1. User Query: "What hardware do I need for Isaac simulations?"
         │
         ▼
2. POST /chat { query: "...", session_id: "abc123" }
         │
         ▼
3. QueryRouter.route(query)
         │
         ├─▶ Intent Classification
         │     │
         │     ▼
         │   Keywords: "hardware", "Isaac"
         │   Pattern match: Hardware domain + Module domain
         │         │
         │         ▼
         │   Decision: Primary → Hardware Agent
         │             Secondary → Module Info (if needed)
         │
         ├─▶ HardwareAgent.run_stream(query, context)
         │     │
         │     ├─▶ RAGSkill.retrieve(query, domain_filter="hardware")
         │     │         │
         │     │         ▼
         │     │   Filtered Qdrant search (hardware-tagged chunks)
         │     │
         │     ├─▶ Generate domain-specific response
         │     │
         │     └─▶ CitationSkill.format(sources)
         │
         └─▶ Return unified response with citations
                   │
                   ▼
4. ChatResponse { answer, citations, agent_used: "hardware" }
```

### Data Flow: Multi-Agent Coordination

```
1. Query: "What sensors does Isaac use and what hardware do they require?"
         │
         ▼
2. QueryRouter.route(query)
         │
         ├─▶ Intent: Multi-domain (Module Info + Hardware)
         │
         ├─▶ Step 1: ModuleInfoAgent.run(partial_query: "sensors Isaac uses")
         │     └─▶ Response A: Isaac sensors overview
         │
         ├─▶ Step 2: HardwareAgent.run(partial_query: "hardware for sensors")
         │     └─▶ Response B: Hardware requirements
         │
         └─▶ Step 3: Synthesize responses A + B
                   │
                   ▼
3. Unified response with combined citations
```

---

## Subsystem Breakdown

### 1. Base Agent (Abstract)

**Purpose**: Define common interface for all subagents.

**File**: `backend/app/agents/base_agent.py`

**Interface**:
```python
class BaseAgent(ABC):
    name: str
    domain: str
    keywords: List[str]

    @abstractmethod
    async def run(self, query: str, context: AgentContext) -> AgentResponse

    @abstractmethod
    async def run_stream(self, query: str, context: AgentContext) -> AsyncGenerator

    def can_handle(self, query: str) -> float:
        """Return confidence score (0-1) for handling this query."""
```

**Key Decisions**:
- All agents inherit from BaseAgent
- `can_handle()` enables router to select best agent
- Streaming support required for real-time responses

### 2. Query Router

**Purpose**: Analyze queries and delegate to appropriate subagent(s).

**File**: `backend/app/agents/router.py`

**Routing Strategy**:
1. **Keyword Matching**: Quick first-pass based on domain keywords
2. **Intent Classification**: Pattern-based (definition vs explanation vs guidance)
3. **Confidence Scoring**: Each agent scores its ability to handle query
4. **Multi-Agent**: Coordinate when query spans domains

**Rules**:
| Pattern | Primary Agent | Notes |
|---------|--------------|-------|
| "What is X", "Define Y" | Glossary | Term definitions |
| "hardware", "specs", "requirements", "GPU" | Hardware | Tech specs |
| "Module N", "ROS 2", "Gazebo", "Isaac", "VLA" | Module Info | Concepts |
| "capstone", "project", "humanoid", "pipeline" | Capstone | Project guidance |
| Mixed signals | Multi-agent | Coordinate response |
| No match | Book Agent | Fallback to general RAG |

### 3. Glossary Agent

**Purpose**: Provide technical term definitions from all modules.

**File**: `backend/app/agents/glossary_agent.py`

**Domain Keywords**: "topic", "node", "TF", "URDF", "SDF", "VLA", "IMU", "LiDAR", etc.

**Behavior**:
- Answer format: Clear definition + module context
- Must indicate when term not found
- Support cross-module term disambiguation

**Example Queries**:
- "What is a topic in ROS 2?"
- "Define digital twin"
- "What does VLA stand for?"

### 4. Hardware Agent

**Purpose**: Provide hardware requirements and recommendations.

**File**: `backend/app/agents/hardware_agent.py`

**Domain Keywords**: "hardware", "workstation", "RTX", "Jetson", "GPU", "RAM", "sensor", "LiDAR", "camera"

**Behavior**:
- Provide specifications (min/recommended)
- Compare options with pros/cons
- Match hardware to use cases

**Example Queries**:
- "What hardware do I need for Isaac?"
- "Should I use RTX workstation or Jetson?"
- "Can I run Gazebo on integrated graphics?"

### 5. Module Info Agent

**Purpose**: Explain concepts from each book module.

**File**: `backend/app/agents/module_info_agent.py`

**Domain Keywords**: "ROS 2", "Gazebo", "Unity", "Isaac", "VLA", "perception", "navigation", "simulation"

**Behavior**:
- Module-aware explanations
- Cross-reference prerequisites
- Indicate when spanning modules

**Example Queries**:
- "How does Isaac handle perception?"
- "Explain ROS 2 nodes and services"
- "How does ROS 2 integrate with Gazebo?"

### 6. Capstone Agent

**Purpose**: Guide students through the Autonomous Humanoid project.

**File**: `backend/app/agents/capstone_agent.py`

**Domain Keywords**: "capstone", "project", "humanoid", "voice command", "Whisper", "path planning", "navigation", "manipulation"

**Behavior**:
- Pipeline-aware guidance (voice → planning → nav → manipulation)
- Milestone tracking
- Troubleshooting assistance

**Example Queries**:
- "How do I connect Whisper to the navigation stack?"
- "What are the capstone milestones?"
- "My humanoid isn't responding to voice commands"

### 7. Shared Skills

**Purpose**: Reusable capabilities across all subagents.

**Files**:
- `citation_skill.py`: Format [Source N] references, extract metadata
- `rag_skill.py`: Domain-filtered vector retrieval
- `context_skill.py`: Session history, follow-up handling

**Key Design**:
- Skills are stateless functions/classes
- Injected into agents via dependency injection
- Can be tested independently

---

## Dependencies & Tools

### New Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| (none required) | - | Uses existing LangChain + Qdrant stack |

### Existing Dependencies (Reused)

| Package | Purpose |
|---------|---------|
| langchain | RAG orchestration |
| langchain-openai | LLM integration |
| qdrant-client | Vector search |
| fastapi | API framework |
| pydantic | Schema validation |

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Router misclassification** | Medium | Medium | Confidence thresholds, fallback to book agent |
| **Multi-agent response incoherence** | Medium | Medium | Clear synthesis prompt, response validation |
| **Agent timeout** | Low | High | Async streaming, timeout per agent, graceful degradation |
| **Duplicate content in agents** | Medium | Low | Shared skills, strict domain boundaries |
| **Integration with existing RAG** | Low | High | Preserve BookAgent as fallback, gradual rollout |

---

## Success Checklist

| Criterion | Test | Pass Condition |
|-----------|------|----------------|
| All agents registered | Unit test | Registry contains 4 agents |
| Router routes correctly | 10 sample queries | 90%+ correct routing |
| Glossary answers terms | Query "What is a topic?" | Returns ROS 2 definition |
| Hardware gives specs | Query "Isaac requirements" | Returns GPU/RAM specs |
| Module Info explains | Query "ROS 2 nodes" | Module 1 content |
| Capstone guides | Query "capstone milestones" | Returns structured list |
| Multi-agent works | Query spanning 2 domains | Coherent combined response |
| Fallback works | Out-of-scope query | Book Agent handles gracefully |
| Citations preserved | Any query | Response includes [Source N] |
| Streaming works | Any query | Real-time token delivery |

---

## Related Documents

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Technical research findings
- [data-model.md](./data-model.md) - Entity definitions
- [quickstart.md](./quickstart.md) - Setup guide
- [contracts/openapi.yaml](./contracts/openapi.yaml) - Updated API contract

---

## Next Steps

1. Run `/sp.tasks` to generate implementation task list
2. Implement BaseAgent and router first
3. Add subagents one at a time (Glossary → Hardware → Module → Capstone)
4. Integration testing with existing RAG pipeline
5. Update frontend chatbot to display agent attribution (optional)
