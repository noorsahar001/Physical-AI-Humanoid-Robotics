# Data Model: Reusable Subagents for Physical AI & Humanoid Robotics

**Feature**: 003-reusable-subagents | **Date**: 2025-12-17

---

## Overview

This document defines the key entities, their relationships, and validation rules for the subagent architecture. These models extend the existing RAG chatbot data model.

---

## Entity Definitions

### 1. BaseAgent (Abstract)

The base class for all domain-specific subagents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Unique agent identifier (e.g., "glossary", "hardware") |
| `domain` | str | Yes | Domain scope description |
| `keywords` | List[str] | Yes | Keywords that trigger this agent |
| `system_prompt` | str | Yes | Agent-specific system prompt |
| `description` | str | Yes | Human-readable description |

**Validation Rules**:
- `name` must be lowercase alphanumeric with underscores only
- `name` must be unique across all registered agents
- `keywords` must contain at least 3 items
- `system_prompt` must reference book content guidelines

**State Transitions**: N/A (stateless)

---

### 2. AgentContext

Context passed to agents when handling queries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | str | Yes | Current session identifier |
| `query` | str | Yes | User's query text |
| `chat_history` | List[Message] | No | Previous conversation messages |
| `selected_text` | str | No | User-highlighted text |
| `domain_filter` | str | No | Restrict retrieval to domain |
| `metadata` | Dict | No | Additional context metadata |

**Validation Rules**:
- `session_id` must be a valid UUID or "anonymous"
- `query` must be between 1 and 2000 characters
- `chat_history` limited to last 10 messages

---

### 3. AgentResponse

Standard response structure from any agent.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `response` | str | Yes | Generated answer text |
| `sources` | List[Citation] | Yes | Source citations (may be empty) |
| `agent_name` | str | Yes | Agent that generated response |
| `confidence` | float | No | Agent's confidence in response (0-1) |
| `metadata` | Dict | No | Additional response metadata |

**Validation Rules**:
- `response` must not be empty
- `agent_name` must match a registered agent
- `confidence` must be between 0.0 and 1.0

---

### 4. RouteResult

Result of query routing decision.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `primary_agent` | str | Yes | Main agent to handle query |
| `secondary_agents` | List[str] | No | Additional agents for multi-domain |
| `confidence` | float | Yes | Routing confidence score |
| `routing_reason` | str | Yes | Explanation of routing decision |
| `is_multi_domain` | bool | Yes | Whether query spans multiple domains |

**Validation Rules**:
- `primary_agent` must be a registered agent name
- `confidence` must be between 0.0 and 1.0
- `routing_reason` must not be empty

---

### 5. AgentRegistry

Central registry for agent discovery and management.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agents` | Dict[str, BaseAgent] | Yes | Registered agents by name |
| `default_agent` | str | Yes | Fallback agent name |

**Validation Rules**:
- `default_agent` must be a registered agent (typically "book")
- At least one agent must be registered

**Methods**:
- `register(agent: BaseAgent)` - Add agent to registry
- `unregister(name: str)` - Remove agent from registry
- `get_agent(name: str) -> Optional[BaseAgent]` - Get agent by name
- `all_agents() -> List[BaseAgent]` - Get all registered agents

---

### 6. Skill (Abstract)

Reusable capability shared across agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Skill identifier |
| `description` | str | Yes | What this skill does |

**Concrete Skills**:

#### 6.1 RAGSkill
| Method | Parameters | Returns |
|--------|------------|---------|
| `retrieve` | query: str, domain_filter: Optional[str], limit: int | List[RetrievedChunk] |

#### 6.2 CitationSkill
| Method | Parameters | Returns |
|--------|------------|---------|
| `format_citations` | chunks: List[RetrievedChunk] | List[Citation] |
| `extract_source_text` | citation: Citation | str |

#### 6.3 ContextSkill
| Method | Parameters | Returns |
|--------|------------|---------|
| `get_history` | session_id: str, limit: int | List[Message] |
| `save_message` | session_id: str, message: Message | None |

---

### 7. RetrievedChunk

Content chunk retrieved from vector database.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | str | Yes | Chunk content |
| `source` | str | Yes | Source file path |
| `title` | str | Yes | Document title |
| `section` | str | No | Section within document |
| `score` | float | Yes | Relevance score (0-1) |
| `domain` | str | No | Domain tag (glossary, hardware, etc.) |
| `metadata` | Dict | No | Additional chunk metadata |

**Validation Rules**:
- `score` must be between 0.0 and 1.0
- `text` must not be empty

---

### 8. Message (Existing - Extended)

Chat message in conversation history.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | str | Yes | "user" or "assistant" |
| `content` | str | Yes | Message content |
| `timestamp` | datetime | No | When message was created |
| `agent_name` | str | No | **New**: Which agent responded |

---

## Entity Relationships

```
┌─────────────────┐
│  AgentRegistry  │
│─────────────────│
│ agents: Dict    │
│ default_agent   │
└────────┬────────┘
         │ contains
         │
         ▼
┌─────────────────┐         ┌─────────────────┐
│   BaseAgent     │◄────────│   QueryRouter   │
│─────────────────│ selects │─────────────────│
│ name            │         │ route(query)    │
│ domain          │         └────────┬────────┘
│ keywords        │                  │
│ run()           │                  │ returns
│ can_handle()    │                  │
└────────┬────────┘                  ▼
         │                  ┌─────────────────┐
         │ uses             │  RouteResult    │
         │                  │─────────────────│
         ▼                  │ primary_agent   │
┌─────────────────┐         │ secondary_agents│
│     Skill       │         │ confidence      │
│─────────────────│         └─────────────────┘
│ RAGSkill        │
│ CitationSkill   │
│ ContextSkill    │
└────────┬────────┘
         │
         │ retrieves
         ▼
┌─────────────────┐         ┌─────────────────┐
│ RetrievedChunk  │────────►│    Citation     │
│─────────────────│ formats │─────────────────│
│ text            │         │ index           │
│ source          │         │ source          │
│ score           │         │ title           │
│ domain          │         │ relevance_score │
└─────────────────┘         └─────────────────┘
```

---

## Domain Enumeration

Defines the valid domains for agents and content tagging.

```python
class AgentDomain(str, Enum):
    GLOSSARY = "glossary"
    HARDWARE = "hardware"
    MODULE_INFO = "module_info"
    CAPSTONE = "capstone"
    BOOK = "book"  # Fallback / general
```

---

## Pydantic Schema Extensions

### ChatResponse (Extended)

```python
class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    query_id: str
    session_id: str
    latency_ms: Optional[int] = None
    # New fields for subagent support
    agent_used: Optional[str] = None
    routing_confidence: Optional[float] = None
```

### AgentInfoResponse (New)

```python
class AgentInfoResponse(BaseModel):
    """Response for /agents endpoint."""
    agents: List[AgentSummary]
    total: int

class AgentSummary(BaseModel):
    """Summary of a registered agent."""
    name: str
    domain: str
    description: str
    keywords: List[str]
```

### RouteRequest (New)

```python
class RouteRequest(BaseModel):
    """Request to get routing decision without executing."""
    query: str

class RouteResponse(BaseModel):
    """Response showing routing decision."""
    primary_agent: str
    secondary_agents: List[str]
    confidence: float
    reason: str
```

---

## Database Considerations

### Vector Database (Qdrant)

**Existing Collection**: `physical_ai_book`

**Payload Schema Extension**:
```json
{
  "text": "...",
  "source": "...",
  "page_title": "...",
  "chunk_id": "...",
  "domain": "glossary|hardware|module_info|capstone|general"  // NEW
}
```

**Migration Required**: Add `domain` field to existing chunks during re-ingestion.

### Session Storage (In-Memory)

No changes required. Session context continues to use existing `DatabaseService`.

---

## Validation Summary

| Entity | Validation Method | Error Handling |
|--------|-------------------|----------------|
| BaseAgent | Pydantic + Abstract | TypeError if abstract methods missing |
| AgentContext | Pydantic | ValidationError with field details |
| AgentResponse | Pydantic | ValidationError |
| RouteResult | Pydantic | ValidationError |
| AgentRegistry | Runtime checks | KeyError if agent not found |

---

## Migration Notes

1. **Existing Chunks**: Need `domain` field added via re-ingestion or batch update
2. **ChatResponse**: New fields are optional, backward compatible
3. **BookAgent**: No changes required, continues as fallback
4. **Session Messages**: Optional `agent_name` field, backward compatible
