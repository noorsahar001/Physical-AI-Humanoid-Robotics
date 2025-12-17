"""
Glossary Agent for technical term definitions.
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


# System prompt for the glossary agent
GLOSSARY_SYSTEM_PROMPT = """You are a Glossary Assistant for the "Physical AI & Humanoid Robotics" book.

Your Role:
1. Provide clear, concise definitions for technical terms
2. Include the module/context where the term is used
3. If a term appears in multiple modules, explain each usage
4. If a term is NOT in the book, say "This term is not defined in this course."

Topics you cover (from the book):
- ROS 2: Topics, nodes, services, actions, TF, URDF, messages
- Gazebo: Digital twin, SDF, world files, plugins
- Isaac: Perception, manipulation, simulation
- VLA: Vision-Language-Action models, neural policies

Response Format:
- Start with a concise definition (1-2 sentences)
- Provide context about which module(s) use this term
- Include any related terms if helpful
- ALWAYS cite sources using [Source N] format

Example Response:
"A **topic** in ROS 2 is a named bus for asynchronous message passing between nodes [Source 1]. Topics use a publish-subscribe pattern where publishers send messages and subscribers receive them without direct connection [Source 2]. This concept is introduced in Module 1 (ROS 2 Fundamentals) and used throughout the book."
"""


class GlossaryAgent(BaseAgent):
    """
    Agent specializing in technical term definitions.

    Handles queries like:
    - "What is a topic in ROS 2?"
    - "Define digital twin"
    - "What does VLA stand for?"
    """

    name = "glossary"
    domain = AgentDomain.GLOSSARY
    description = "Provides definitions for technical terms from ROS 2, Gazebo, Isaac, and VLA modules"

    # Keywords that trigger this agent
    keywords = [
        # Definition patterns
        "what is", "define", "meaning of", "definition", "what does", "what are",
        "explain term", "terminology",
        # ROS 2 terms
        "topic", "node", "service", "action", "TF", "URDF", "message", "publisher",
        "subscriber", "launch", "parameter", "lifecycle",
        # Gazebo terms
        "digital twin", "SDF", "world file", "plugin", "physics engine",
        # Isaac terms
        "perception", "manipulation", "isaac sim", "omniverse",
        # VLA terms
        "VLA", "vision language", "neural policy", "imitation learning",
        # Sensor terms
        "IMU", "LiDAR", "depth camera", "RGB camera", "encoder",
        # General robotics
        "kinematics", "dynamics", "trajectory", "control loop", "state estimation"
    ]

    system_prompt = GLOSSARY_SYSTEM_PROMPT

    def __init__(
        self,
        rag_skill: RAGSkill,
        citation_skill: CitationSkill,
        context_skill: ContextSkill,
    ):
        """
        Initialize the glossary agent with required skills.

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
            "temperature": 0.2,  # Lower temperature for precise definitions
            "max_tokens": 1024,
            "streaming": True,
        }
        if settings.LLM_BASE_URL:
            llm_kwargs["openai_api_base"] = settings.LLM_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)

    def can_handle(self, query: str) -> float:
        """
        Return confidence score for handling this query.

        Boosts score for definition-style queries.
        """
        # Start with base keyword matching
        base_score = super().can_handle(query)

        query_lower = query.lower()

        # Strong boost for explicit definition patterns
        definition_phrases = [
            "what is a", "what is an", "what is the",
            "define ", "definition of", "meaning of",
            "what does ", "what are ", "explain the term"
        ]
        for phrase in definition_phrases:
            if phrase in query_lower:
                base_score += 0.4
                break

        # Moderate boost for term lookups
        if "term" in query_lower or "glossary" in query_lower:
            base_score += 0.2

        return min(base_score, 1.0)

    async def run(
        self,
        query: str,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Run the glossary agent and return complete response.

        Args:
            query: The user's term definition question
            context: Agent context with session info

        Returns:
            AgentResponse with definition and citations
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
        Run the glossary agent and stream the response.

        Args:
            query: The user's term definition question
            context: Agent context with session info

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        logger.info(f"GlossaryAgent processing: {query[:100]}...")

        try:
            # Retrieve relevant content with glossary domain filter
            retrieved_content = self.rag_skill.retrieve(
                query=query,
                domain_filter="glossary",  # Try domain filter first
                limit=5,
            )

            # If no glossary-specific content, try general retrieval
            if not retrieved_content:
                retrieved_content = self.rag_skill.retrieve(
                    query=query,
                    limit=5,
                )

            # Build context with citations
            context_text = self.citation_skill.build_context_with_citations(
                retrieved_content,
                context.selected_text,
            )

            # Build messages for LLM
            messages = [SystemMessage(content=self.system_prompt)]

            # Add chat history
            for msg in context.chat_history[-5:]:  # Limit history
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

Please provide a clear definition based on the book content. If this term is not in the book, say so clearly. Always cite sources using [Source N] format."""

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
            logger.error(f"Error in GlossaryAgent: {e}")
            yield ("text", f"Sorry, an error occurred while looking up this term: {str(e)}")
            yield ("end", "")

    def extract_term(self, query: str) -> str:
        """
        Extract the term being asked about from the query.

        Args:
            query: The user's question

        Returns:
            The extracted term or the original query
        """
        query_lower = query.lower()

        # Patterns to extract term from
        patterns = [
            ("what is a ", "?"),
            ("what is an ", "?"),
            ("what is the ", "?"),
            ("what is ", "?"),
            ("define ", ""),
            ("what does ", " mean"),
            ("meaning of ", ""),
            ("definition of ", ""),
        ]

        for prefix, suffix in patterns:
            if prefix in query_lower:
                start = query_lower.index(prefix) + len(prefix)
                if suffix and suffix in query_lower[start:]:
                    end = query_lower.index(suffix, start)
                    return query[start:end].strip()
                else:
                    return query[start:].strip().rstrip("?")

        return query
