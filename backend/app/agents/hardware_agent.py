"""
Hardware Agent for hardware requirements and setup guidance.
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


# System prompt for the hardware agent
HARDWARE_SYSTEM_PROMPT = """You are a Hardware Setup Assistant for the "Physical AI & Humanoid Robotics" book.

Your Role:
1. Provide hardware requirements and specifications
2. Give recommendations based on use case (simulation, edge deployment, lab work)
3. Compare hardware options (RTX workstation vs Jetson, etc.)
4. Explain sensor requirements and compatibility

Topics you cover (from the book):
- Workstation Requirements: CPU, GPU, RAM for simulation
- NVIDIA GPUs: RTX series specifications for Isaac/Gazebo
- Jetson Edge Kits: Orin, Xavier, Nano specifications
- Sensors: LiDAR, cameras, IMUs, encoders
- Networking: ROS 2 communication setup

Response Format:
- Provide specific specifications when available
- Include minimum vs recommended specs
- Explain trade-offs between options
- ALWAYS cite sources using [Source N] format

Example Response:
"For Isaac Sim, NVIDIA recommends:
- **Minimum**: RTX 2070, 16GB RAM, Intel i7 [Source 1]
- **Recommended**: RTX 3080+, 32GB RAM, AMD Ryzen 9 [Source 2]

For edge deployment on Jetson Orin:
- 8GB-64GB RAM variants available
- Suitable for real-time inference [Source 3]"
"""


class HardwareAgent(BaseAgent):
    """
    Agent specializing in hardware requirements and setup.

    Handles queries like:
    - "What GPU do I need for Isaac?"
    - "Jetson vs RTX workstation comparison"
    - "What sensors are needed for SLAM?"
    """

    name = "hardware"
    domain = AgentDomain.HARDWARE
    description = "Provides hardware requirements, specifications, and setup guidance for robotics development"

    # Keywords that trigger this agent
    keywords = [
        # Hardware components
        "hardware", "GPU", "CPU", "RAM", "memory", "processor", "graphics card",
        "workstation", "computer", "machine", "system requirements",
        # NVIDIA specific
        "RTX", "NVIDIA", "CUDA", "Jetson", "Orin", "Xavier", "Nano", "AGX",
        # Specifications
        "requirements", "specs", "specifications", "minimum", "recommended",
        "how much", "what hardware", "can i run", "system specs",
        # Sensors
        "LiDAR", "camera", "sensor", "IMU", "encoder", "depth camera",
        "Intel RealSense", "ZED", "Velodyne",
        # Comparison
        "vs", "versus", "compare", "comparison", "better", "difference between",
        # Setup
        "setup", "install", "configure", "build"
    ]

    system_prompt = HARDWARE_SYSTEM_PROMPT

    def __init__(
        self,
        rag_skill: RAGSkill,
        citation_skill: CitationSkill,
        context_skill: ContextSkill,
    ):
        """
        Initialize the hardware agent with required skills.

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
            "temperature": 0.3,
            "max_tokens": 1500,
            "streaming": True,
        }
        if settings.LLM_BASE_URL:
            llm_kwargs["openai_api_base"] = settings.LLM_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)

    def can_handle(self, query: str) -> float:
        """
        Return confidence score for handling this query.

        Boosts score for hardware-specific patterns.
        """
        base_score = super().can_handle(query)
        query_lower = query.lower()

        # Strong boost for hardware-specific patterns
        hardware_phrases = [
            "what hardware", "hardware requirements", "gpu requirements",
            "cpu requirements", "ram requirements", "system requirements",
            "what specs", "minimum requirements", "recommended specs",
            "can i run", "will it run", "do i need",
            "jetson vs", "rtx vs", "compare hardware"
        ]
        for phrase in hardware_phrases:
            if phrase in query_lower:
                base_score += 0.35
                break

        # Moderate boost for sensor queries
        sensor_terms = ["sensor", "lidar", "camera", "imu", "realsense", "zed"]
        if any(term in query_lower for term in sensor_terms):
            base_score += 0.2

        return min(base_score, 1.0)

    async def run(
        self,
        query: str,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Run the hardware agent and return complete response.

        Args:
            query: The user's hardware question
            context: Agent context with session info

        Returns:
            AgentResponse with hardware guidance and citations
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
        Run the hardware agent and stream the response.

        Args:
            query: The user's hardware question
            context: Agent context with session info

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        logger.info(f"HardwareAgent processing: {query[:100]}...")

        try:
            # Retrieve relevant content with hardware domain filter
            retrieved_content = self.rag_skill.retrieve(
                query=query,
                domain_filter="hardware",
                limit=5,
            )

            # If no hardware-specific content, try general retrieval
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

Please provide specific hardware recommendations based on the book content. Include minimum and recommended specs when available. If comparing options, explain trade-offs. Always cite sources using [Source N] format."""

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
            logger.error(f"Error in HardwareAgent: {e}")
            yield ("text", f"Sorry, an error occurred while processing your hardware question: {str(e)}")
            yield ("end", "")

    def detect_comparison_query(self, query: str) -> bool:
        """
        Detect if the query is asking for a comparison.

        Args:
            query: The user's question

        Returns:
            True if this is a comparison query
        """
        comparison_terms = ["vs", "versus", "compare", "comparison", "or", "better", "difference"]
        query_lower = query.lower()
        return any(term in query_lower for term in comparison_terms)
