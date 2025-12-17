"""
Module Info Agent for module-specific concept explanations.
Constitution v2.0.0: Principle XI (Domain-Specific Agent Isolation)
"""

from typing import Dict, Any, List, AsyncGenerator
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.config import settings
from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentDomain
from app.skills.rag_skill import RAGSkill
from app.skills.citation_skill import CitationSkill
from app.skills.context_skill import ContextSkill

logger = logging.getLogger(__name__)


# System prompt for the module info agent
MODULE_INFO_SYSTEM_PROMPT = """You are a Module Explanation Assistant for the "Physical AI & Humanoid Robotics" book.

Your Role:
1. Explain concepts from each book module in depth
2. Provide step-by-step explanations when appropriate
3. Include relevant code examples from the book
4. Cross-reference related concepts across modules

Book Modules:
- Module 1: ROS 2 Fundamentals (nodes, topics, services, actions, TF, URDF)
- Module 2: Gazebo & Unity Simulation (digital twins, physics, sensors)
- Module 3: NVIDIA Isaac (perception, manipulation, Isaac Sim)
- Module 4: VLA Models (vision-language-action, neural policies)
- Capstone: Autonomous Humanoid Project (integration)

Response Format:
- Start with a concise overview
- Break down complex concepts into steps
- Include code snippets when relevant (use markdown)
- Mention prerequisites from earlier modules
- ALWAYS cite sources using [Source N] format

Example Response:
"ROS 2 nodes communicate through **topics** and **services** [Source 1].

**Topics** use publish-subscribe for streaming data:
```python
# Example publisher from Module 1
self.publisher = self.create_publisher(String, 'topic_name', 10)
```
[Source 2]

**Services** use request-response for synchronous calls:
```python
# Example service client
self.client = self.create_client(AddTwoInts, 'add_two_ints')
```
[Source 3]

This builds on the node lifecycle concepts from Chapter 2."
"""


class ModuleInfoAgent(BaseAgent):
    """
    Agent specializing in module-specific concept explanations.

    Handles queries like:
    - "How does ROS 2 handle communication?"
    - "Explain Isaac perception pipeline"
    - "How do I set up a Gazebo simulation?"
    """

    name = "module_info"
    domain = AgentDomain.MODULE_INFO
    description = "Provides explanations for concepts from each book module (ROS 2, Gazebo, Isaac, VLA)"

    # Keywords that trigger this agent
    keywords = [
        # Explanation patterns
        "how does", "how do", "explain", "what happens", "why does",
        "how to", "walk me through", "step by step", "tutorial",
        # ROS 2 module
        "ROS 2", "ROS2", "ros", "node", "topic", "service", "action",
        "publisher", "subscriber", "launch file", "parameter",
        # Gazebo module
        "Gazebo", "simulation", "world file", "physics", "Unity",
        # Isaac module
        "Isaac", "Isaac Sim", "Omniverse", "perception", "manipulation",
        # VLA module
        "VLA", "vision language", "neural policy", "imitation",
        "policy learning", "robot learning",
        # General concepts
        "module", "chapter", "concept", "example", "code"
    ]

    system_prompt = MODULE_INFO_SYSTEM_PROMPT

    def __init__(
        self,
        rag_skill: RAGSkill,
        citation_skill: CitationSkill,
        context_skill: ContextSkill,
    ):
        """
        Initialize the module info agent with required skills.

        Args:
            rag_skill: For retrieving relevant book content
            citation_skill: For formatting citations
            context_skill: For session management
        """
        self.rag_skill = rag_skill
        self.citation_skill = citation_skill
        self.context_skill = context_skill

        # Configure LLM
        api_key = settings.active_api_key
        llm_kwargs = {
            "model": settings.LLM_MODEL,
            "openai_api_key": api_key,
            "temperature": 0.4,  # Slightly higher for explanations
            "max_tokens": 2000,  # More tokens for detailed explanations
            "streaming": True,
        }
        if settings.LLM_BASE_URL:
            llm_kwargs["openai_api_base"] = settings.LLM_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)

    def can_handle(self, query: str) -> float:
        """
        Return confidence score for handling this query.

        Boosts score for explanation-style patterns.
        """
        base_score = super().can_handle(query)
        query_lower = query.lower()

        # Strong boost for explanation patterns
        explanation_phrases = [
            "how does", "how do", "explain", "walk me through",
            "step by step", "tutorial", "how to", "how can i",
            "what happens when", "why does", "show me how"
        ]
        for phrase in explanation_phrases:
            if phrase in query_lower:
                base_score += 0.3
                break

        # Moderate boost for module-specific keywords
        module_terms = ["ros 2", "ros2", "gazebo", "isaac", "vla", "module", "chapter"]
        if any(term in query_lower for term in module_terms):
            base_score += 0.2

        return min(base_score, 1.0)

    async def run(
        self,
        query: str,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Run the module info agent and return complete response.

        Args:
            query: The user's module question
            context: Agent context with session info

        Returns:
            AgentResponse with explanation and citations
        """
        full_response = ""
        sources = []

        async for chunk_type, content in self.run_stream(query, context):
            if chunk_type == "text":
                full_response += content
            elif chunk_type == "source":
                sources.append(content)

        return AgentResponse(
            response=full_response,
            sources=sources,
            agent_name=self.name,
            confidence=1.0,
        )

    async def run_stream(
        self,
        query: str,
        context: AgentContext,
    ) -> AsyncGenerator[tuple, None]:
        """
        Run the module info agent and stream the response.

        Args:
            query: The user's module question
            context: Agent context with session info

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        logger.info(f"ModuleInfoAgent processing: {query[:100]}...")

        try:
            # Detect which module the query relates to
            module = self._detect_module(query)

            # Retrieve relevant content (module-specific if detected)
            domain_filter = f"module_{module}" if module else None
            retrieved_content = self.rag_skill.retrieve(
                query=query,
                domain_filter=domain_filter,
                limit=6,  # More context for explanations
            )

            # If no module-specific content, try general retrieval
            if not retrieved_content:
                retrieved_content = self.rag_skill.retrieve(
                    query=query,
                    limit=6,
                )

            # Build context with citations
            context_text = self.citation_skill.build_context_with_citations(
                retrieved_content,
                context.selected_text,
            )

            # Build messages for LLM
            messages = [SystemMessage(content=self.system_prompt)]

            # Add chat history
            for msg in context.chat_history[-5:]:
                role = msg.get("role", "user")
                content_text = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content_text))
                elif role == "assistant":
                    messages.append(AIMessage(content=content_text))

            # Add current query with context
            user_message = f"""Context from the book:
{context_text}

User Question: {query}

Please provide a clear explanation based on the book content. Include code examples when relevant, and mention any prerequisites from earlier modules. Always cite sources using [Source N] format."""

            messages.append(HumanMessage(content=user_message))

            # Stream the response
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield ("text", chunk.content)

            # Yield citations
            if retrieved_content:
                citations = self.citation_skill.format_citations(retrieved_content)
                for citation in citations:
                    yield ("source", citation)

            yield ("end", "")

        except Exception as e:
            logger.error(f"Error in ModuleInfoAgent: {e}")
            yield ("text", f"Sorry, an error occurred while explaining this concept: {str(e)}")
            yield ("end", "")

    def _detect_module(self, query: str) -> str:
        """
        Detect which module the query relates to.

        Args:
            query: The user's question

        Returns:
            Module identifier or empty string
        """
        query_lower = query.lower()

        module_keywords = {
            "ros2": ["ros 2", "ros2", "node", "topic", "service", "action", "launch", "urdf"],
            "gazebo": ["gazebo", "simulation", "world file", "sdf", "physics", "unity"],
            "isaac": ["isaac", "isaac sim", "omniverse", "perception", "manipulation"],
            "vla": ["vla", "vision language", "neural policy", "imitation learning"],
        }

        for module, keywords in module_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return module

        return ""
