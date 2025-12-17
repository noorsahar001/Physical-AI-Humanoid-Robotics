# Research: Reusable Subagents for Physical AI & Humanoid Robotics

**Feature**: 003-reusable-subagents | **Date**: 2025-12-17

---

## Overview

This document captures technical research findings for implementing modular subagents using Claude Code Subagents and Agent Skills. All decisions are informed by the existing codebase (002-rag-chatbot) and the Constitution v2.0.0.

---

## R1: Subagent Architecture Patterns

### Decision: Inheritance-Based Agent Framework

**What was chosen**: Abstract base class (`BaseAgent`) with concrete implementations for each domain agent.

**Rationale**:
- Ensures consistent interface across all agents (Constitution X)
- Enables registry-based discovery (Constitution XIII)
- Supports dependency injection of shared skills
- Existing `BookAgent` demonstrates LangChain integration pattern

**Alternatives considered**:
1. **Composition-only (no inheritance)**: More flexible but harder to enforce interface contracts
2. **Protocol-based (structural typing)**: Pythonic but less explicit for new developers
3. **Plugin architecture**: Over-engineered for 4 initial agents

**Code Reference**: `backend/app/agents/book_agent.py:42-68` shows the pattern to follow.

---

## R2: Query Routing Strategy

### Decision: Hybrid Keyword + Intent Classification Router

**What was chosen**: Two-phase routing:
1. **Fast path**: Keyword matching for high-confidence domain signals
2. **Fallback**: Intent classification for ambiguous queries

**Rationale**:
- Meets <2s routing performance goal
- Keyword matching handles 70-80% of queries quickly
- Intent classification provides nuance for edge cases
- No ML model dependency (avoids latency and complexity)

**Alternatives considered**:
1. **Pure LLM-based routing**: Accurate but adds 1-3s latency per query
2. **Pure keyword matching**: Fast but misses nuanced queries
3. **Vector similarity routing**: Requires separate embeddings for routing

**Routing Logic**:
```python
def route(query: str) -> RouteResult:
    # Phase 1: Keyword matching
    keyword_scores = {
        agent.name: agent.can_handle(query)
        for agent in registry.agents
    }

    max_score = max(keyword_scores.values())
    if max_score >= CONFIDENCE_THRESHOLD:  # 0.7
        return RouteResult(agent=best_agent, confidence=max_score)

    # Phase 2: Intent classification (for ambiguous queries)
    intent = classify_intent(query)  # definition | explanation | guidance
    return RouteResult(agent=intent_to_agent[intent], confidence=0.5)
```

---

## R3: Domain Boundary Definitions

### Decision: Strict Domain Isolation with Glossary Overlap

**What was chosen**:

| Agent | Primary Domain | Boundary Rules |
|-------|----------------|----------------|
| Glossary | Term definitions | Handles "What is X?" for ANY domain term |
| Hardware | Physical components | Handles specs, requirements, comparisons |
| Module Info | Conceptual explanations | Handles "How does X work?" for modules |
| Capstone | Project integration | Handles pipeline, milestones, troubleshooting |

**Rationale**:
- Glossary is intentionally broad (Constitution XI allows cross-domain for glossary)
- Clear handoff rules prevent confusion
- Students' query patterns map naturally to these domains

**Overlap Resolution**:
- "What is a topic?" → Glossary (definition-style query)
- "How do ROS 2 topics work?" → Module Info (explanation-style)
- "What hardware supports ROS 2?" → Hardware (specs-style)

---

## R4: Shared Skills Design

### Decision: Stateless Skill Functions with Service Injection

**What was chosen**: Skills as standalone modules with dependencies injected.

**Skills Identified**:

| Skill | Purpose | Dependencies |
|-------|---------|--------------|
| `citation_skill` | Format [Source N] references | None |
| `rag_skill` | Domain-filtered retrieval | QdrantService, EmbeddingService |
| `context_skill` | Session history | DatabaseService |

**Rationale**:
- Avoids code duplication across agents
- Skills testable in isolation
- Matches existing service injection pattern (`backend/app/services/`)

**Alternatives considered**:
1. **Agent mixins**: Tighter coupling, harder to test
2. **Skill classes with state**: Unnecessary complexity for these operations
3. **Skill registry**: Over-engineered for 3 skills

**Implementation Pattern**:
```python
# In agent
class GlossaryAgent(BaseAgent):
    def __init__(self, rag_skill: RAGSkill, citation_skill: CitationSkill):
        self.rag_skill = rag_skill
        self.citation_skill = citation_skill
```

---

## R5: Multi-Agent Coordination

### Decision: Sequential Synthesis with Single Response

**What was chosen**: When a query spans multiple domains:
1. Router identifies relevant agents
2. Agents execute sequentially (not parallel)
3. Responses synthesized into unified answer

**Rationale**:
- Simpler implementation than parallel coordination
- Response coherence easier to achieve
- User sees single unified response (Constitution XII)
- Parallel execution can be added later if needed

**Alternatives considered**:
1. **Parallel execution**: Complex error handling, response merging
2. **Agent chaining**: One agent hands off to another (order-dependent)
3. **No multi-agent**: Limits query capabilities

**Synthesis Approach**:
```python
async def handle_multi_domain(query, agents):
    responses = []
    for agent in agents:
        partial = await agent.run(query)
        responses.append(partial)

    return synthesize_responses(query, responses)
```

---

## R6: Agent Registration and Discovery

### Decision: Explicit Registry with Lazy Loading

**What was chosen**: Central `AgentRegistry` class with explicit registration.

**Rationale**:
- Predictable agent availability
- Easy to test which agents are registered
- Supports future dynamic registration (Constitution XIII)

**Implementation**:
```python
# backend/app/agents/__init__.py
class AgentRegistry:
    _agents: Dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent: BaseAgent):
        cls._agents[agent.name] = agent

    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        return cls._agents.get(name)

    @classmethod
    def all_agents(cls) -> List[BaseAgent]:
        return list(cls._agents.values())
```

---

## R7: Existing RAG Integration

### Decision: Preserve BookAgent as Fallback

**What was chosen**:
- `BookAgent` remains unchanged as fallback
- New router sits above BookAgent
- Subagents reuse same RAG infrastructure via skills

**Rationale**:
- Zero breaking changes to existing functionality
- Gradual rollout possible (feature flag)
- Fallback ensures no query goes unanswered

**Integration Point**:
```python
# backend/app/services/rag_pipeline.py
class RAGPipeline:
    def __init__(self, ..., router: QueryRouter):
        self.router = router  # New
        self.agent = BookAgent(...)  # Preserved as fallback

    async def run_rag_stream(self, ...):
        route_result = self.router.route(query)
        if route_result.agent:
            return await route_result.agent.run_stream(query, context)
        return await self.agent.run_stream(query, ...)  # Fallback
```

---

## R8: Domain-Filtered Retrieval

### Decision: Metadata Filtering in Qdrant Queries

**What was chosen**: Add `domain` tag to chunk payloads, filter during retrieval.

**Rationale**:
- Hardware agent only needs hardware-related chunks
- Reduces noise in LLM context
- Qdrant supports payload filtering efficiently

**Implementation**:
```python
# RAGSkill.retrieve()
def retrieve(query: str, domain_filter: Optional[str] = None):
    filter_condition = None
    if domain_filter:
        filter_condition = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain_filter))]
        )

    return qdrant_service.search_vectors(
        query_vector=embedding,
        filter=filter_condition,
        limit=5
    )
```

**Required Ingestion Change**: Book content must be tagged with domain metadata during ingestion.

---

## R9: Response Schema Extensions

### Decision: Add `agent_used` Field to ChatResponse

**What was chosen**: Extend existing `ChatResponse` with agent attribution.

**Rationale**:
- Transparency for debugging and analytics
- Optional for frontend display
- Backward compatible (nullable field)

**Schema Update**:
```python
class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    query_id: str
    session_id: str
    latency_ms: Optional[int]
    agent_used: Optional[str] = None  # New: "glossary", "hardware", etc.
```

---

## R10: Testing Strategy

### Decision: Unit Tests per Agent + Integration Test for Router

**What was chosen**:
- Each agent has dedicated test file
- Router tested with sample query matrix
- Integration test covers full flow

**Test Matrix**:

| Query | Expected Agent | Test File |
|-------|----------------|-----------|
| "What is a topic?" | Glossary | test_glossary_agent.py |
| "Isaac hardware requirements" | Hardware | test_hardware_agent.py |
| "How does ROS 2 work?" | Module Info | test_module_info_agent.py |
| "Capstone milestones" | Capstone | test_capstone_agent.py |
| "Unknown random query" | BookAgent (fallback) | test_router.py |

**Rationale**:
- Agents testable in isolation (mock RAG skill)
- Router tests validate routing logic
- Integration test catches glue issues

---

## Summary of Key Decisions

| Area | Decision | Confidence |
|------|----------|------------|
| Agent Architecture | Inheritance from BaseAgent | High |
| Routing | Keyword + Intent hybrid | High |
| Skill Pattern | Stateless with injection | High |
| Multi-Agent | Sequential synthesis | Medium |
| RAG Integration | Preserve BookAgent fallback | High |
| Domain Filtering | Qdrant metadata filtering | High |
| Testing | Unit per agent + integration | High |

---

## Open Questions (Resolved)

1. **Q**: Should we use LLM for routing?
   **A**: No, keyword + intent is sufficient and faster.

2. **Q**: How to handle ambiguous queries?
   **A**: Intent classification as fallback, then BookAgent.

3. **Q**: Parallel or sequential multi-agent?
   **A**: Sequential for simplicity, parallel as future optimization.

---

## References

- Constitution v2.0.0: `.specify/memory/constitution.md`
- Existing BookAgent: `backend/app/agents/book_agent.py`
- Existing RAG Pipeline: `backend/app/services/rag_pipeline.py`
- LangChain Agents: https://python.langchain.com/docs/concepts/agents/
