# Quickstart: Reusable Subagents for Physical AI & Humanoid Robotics

**Feature**: 003-reusable-subagents | **Date**: 2025-12-17

---

## Prerequisites

Before starting, ensure you have:

- [ ] Completed Part 1-3 setup (RAG chatbot working)
- [ ] Python 3.13 installed
- [ ] Backend virtual environment activated
- [ ] Qdrant running (Docker or Cloud)
- [ ] Environment variables configured (`.env` file)

---

## Quick Verification

Verify the existing RAG chatbot is working:

```bash
# From project root
cd backend

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Start the server
uvicorn main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "qdrant": {"status": "up"},
    "llm": {"status": "up"}
  }
}
```

---

## Step 1: Create Agent Directory Structure

```bash
# From backend/app directory
mkdir -p agents skills

# Create __init__.py files
touch agents/__init__.py
touch skills/__init__.py
```

---

## Step 2: Implement Base Agent

Create `backend/app/agents/base_agent.py`:

```python
"""Base class for all domain-specific subagents."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator


class BaseAgent(ABC):
    """Abstract base class defining the subagent interface."""

    name: str
    domain: str
    keywords: List[str]
    system_prompt: str
    description: str

    @abstractmethod
    async def run(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run the agent and return complete response."""
        pass

    @abstractmethod
    async def run_stream(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> AsyncGenerator[tuple, None]:
        """Run the agent and stream the response."""
        pass

    def can_handle(self, query: str) -> float:
        """Return confidence score (0-1) for handling this query."""
        query_lower = query.lower()
        matches = sum(1 for kw in self.keywords if kw.lower() in query_lower)
        return min(matches / 3.0, 1.0)  # Cap at 1.0
```

---

## Step 3: Implement Query Router

Create `backend/app/agents/router.py`:

```python
"""Query router for subagent delegation."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class RouteResult:
    """Result of routing decision."""
    primary_agent: str
    secondary_agents: List[str]
    confidence: float
    reason: str
    is_multi_domain: bool = False


class QueryRouter:
    """Routes queries to appropriate subagents."""

    CONFIDENCE_THRESHOLD = 0.3

    def __init__(self, registry):
        self.registry = registry

    def route(self, query: str) -> RouteResult:
        """Determine which agent(s) should handle the query."""
        scores = {}
        for agent in self.registry.all_agents():
            scores[agent.name] = agent.can_handle(query)

        # Sort by score descending
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_agents or sorted_agents[0][1] < self.CONFIDENCE_THRESHOLD:
            return RouteResult(
                primary_agent="book",  # Fallback
                secondary_agents=[],
                confidence=0.0,
                reason="No agent matched with sufficient confidence"
            )

        primary = sorted_agents[0]
        secondary = [
            name for name, score in sorted_agents[1:3]
            if score >= self.CONFIDENCE_THRESHOLD
        ]

        return RouteResult(
            primary_agent=primary[0],
            secondary_agents=secondary,
            confidence=primary[1],
            reason=f"Matched {primary[0]} agent with confidence {primary[1]:.2f}",
            is_multi_domain=len(secondary) > 0
        )
```

---

## Step 4: Implement Glossary Agent

Create `backend/app/agents/glossary_agent.py`:

```python
"""Glossary Agent for technical term definitions."""

from typing import Dict, Any, AsyncGenerator
from app.agents.base_agent import BaseAgent


class GlossaryAgent(BaseAgent):
    """Agent specializing in technical term definitions."""

    name = "glossary"
    domain = "Technical term definitions"
    description = "Provides definitions for technical terms from ROS 2, Gazebo, Isaac, and VLA"
    keywords = [
        "what is", "define", "meaning of", "definition",
        "topic", "node", "service", "action", "TF", "URDF", "SDF",
        "VLA", "IMU", "LiDAR", "depth camera", "digital twin"
    ]

    system_prompt = """You are a glossary assistant for the Physical AI & Humanoid Robotics book.

Your role:
1. Provide clear, concise definitions for technical terms
2. Include the module/context where the term is used
3. If a term appears in multiple modules, explain each usage
4. If a term is NOT in the book, say "This term is not defined in this course."

Always cite sources using [Source N] format.
"""

    def __init__(self, rag_skill, citation_skill):
        self.rag_skill = rag_skill
        self.citation_skill = citation_skill

    async def run(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass

    async def run_stream(self, query: str, context: Dict[str, Any]) -> AsyncGenerator[tuple, None]:
        # Implementation here
        pass
```

---

## Step 5: Register Agents

Update `backend/app/agents/__init__.py`:

```python
"""Agent registry and exports."""

from typing import Dict, Optional, List
from app.agents.base_agent import BaseAgent


class AgentRegistry:
    """Central registry for agent discovery."""

    _agents: Dict[str, BaseAgent] = {}
    _default_agent: str = "book"

    @classmethod
    def register(cls, agent: BaseAgent):
        """Register an agent."""
        cls._agents[agent.name] = agent

    @classmethod
    def unregister(cls, name: str):
        """Remove an agent from registry."""
        cls._agents.pop(name, None)

    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return cls._agents.get(name)

    @classmethod
    def all_agents(cls) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(cls._agents.values())

    @classmethod
    def default_agent(cls) -> Optional[BaseAgent]:
        """Get the fallback agent."""
        return cls._agents.get(cls._default_agent)


# Export for convenience
from app.agents.base_agent import BaseAgent
from app.agents.router import QueryRouter, RouteResult
```

---

## Step 6: Update RAG Pipeline

Modify `backend/app/services/rag_pipeline.py` to use the router:

```python
# Add to imports
from app.agents import AgentRegistry, QueryRouter

# Add to __init__
self.router = QueryRouter(AgentRegistry)

# Modify run_rag_stream to use routing
async def run_rag_stream(self, session_id: str, query: str, ...):
    route_result = self.router.route(query)

    if route_result.primary_agent != "book":
        agent = AgentRegistry.get_agent(route_result.primary_agent)
        if agent:
            context = {"session_id": session_id, "chat_history": ...}
            async for chunk in agent.run_stream(query, context):
                yield chunk
            return

    # Fallback to existing BookAgent
    async for chunk in self.agent.run_stream(query, ...):
        yield chunk
```

---

## Step 7: Test Individual Agents

```bash
# Run tests
pytest tests/agents/test_glossary_agent.py -v

# Test routing
pytest tests/agents/test_router.py -v
```

---

## Step 8: Test Full Integration

```bash
# Start server
uvicorn main:app --reload

# Test glossary routing
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a topic in ROS 2?"}'

# Check which agent was used
# Response should include: "agent_used": "glossary"
```

---

## Verification Checklist

After completing setup, verify:

- [ ] `GET /health` returns healthy with agents status
- [ ] `GET /agents` lists all 4 subagents
- [ ] Glossary query routes to glossary agent
- [ ] Hardware query routes to hardware agent
- [ ] Module query routes to module_info agent
- [ ] Capstone query routes to capstone agent
- [ ] Unknown query falls back to book agent
- [ ] Citations are included in responses
- [ ] Streaming works for all agents

---

## Troubleshooting

### Agent not found
```
Error: Agent 'glossary' not registered
```
**Solution**: Ensure agent is registered in `__init__.py` startup

### Routing always falls back
```
Routing reason: No agent matched with sufficient confidence
```
**Solution**: Check agent keywords list, lower `CONFIDENCE_THRESHOLD`

### Import errors
```
ImportError: cannot import name 'BaseAgent'
```
**Solution**: Verify all `__init__.py` files export correctly

---

## Next Steps

1. Implement remaining agents (Hardware, Module Info, Capstone)
2. Add domain filtering to RAG retrieval
3. Implement multi-agent coordination
4. Add agent-specific tests
5. Run `/sp.tasks` to generate detailed task list

---

## Related Documents

- [plan.md](./plan.md) - Full implementation plan
- [research.md](./research.md) - Technical decisions
- [data-model.md](./data-model.md) - Entity definitions
- [contracts/openapi.yaml](./contracts/openapi.yaml) - API specification
