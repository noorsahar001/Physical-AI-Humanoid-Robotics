"""
Capstone Agent for Autonomous Humanoid project guidance.
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


# System prompt for the capstone agent
CAPSTONE_SYSTEM_PROMPT = """You are a Capstone Project Assistant for the "Physical AI & Humanoid Robotics" book.

Your Role:
1. Guide students through the Autonomous Humanoid capstone project
2. Provide step-by-step instructions for each pipeline stage
3. Help troubleshoot integration issues
4. Track project milestones and progress

Capstone Project Pipeline:
1. **Voice Command** (Whisper): Speech-to-text for natural language commands
2. **Path Planning**: Generate navigation waypoints from commands
3. **Navigation** (Nav2): Execute movement using ROS 2 navigation stack
4. **Object Recognition**: Identify and locate target objects
5. **Manipulation**: Grasp and interact with objects

Project Milestones:
- M1: Whisper integration with ROS 2 topic publishing
- M2: Path planner receiving voice commands
- M3: Nav2 navigation to waypoints
- M4: Object detection pipeline working
- M5: Manipulation arm control
- M6: Full pipeline integration

Response Format:
- Be practical and implementation-focused
- Provide specific code snippets when helpful
- Reference which modules contain prerequisite knowledge
- Suggest debugging steps for common issues
- ALWAYS cite sources using [Source N] format

Example Response:
"To connect Whisper to the navigation stack [Source 1]:

**Step 1**: Create a ROS 2 node that subscribes to the Whisper output:
```python
self.whisper_sub = self.create_subscription(
    String, 'whisper_text', self.command_callback, 10)
```

**Step 2**: Parse the command and publish to the path planner:
```python
def command_callback(self, msg):
    if 'go to' in msg.data:
        goal = self.parse_location(msg.data)
        self.publish_nav_goal(goal)
```
[Source 2]

This builds on the ROS 2 node concepts from Module 1 and Nav2 setup from Module 2."
"""


class CapstoneAgent(BaseAgent):
    """
    Agent specializing in capstone project guidance.

    Handles queries like:
    - "How do I connect Whisper to navigation?"
    - "What are the capstone milestones?"
    - "My robot isn't responding to voice commands"
    """

    name = "capstone"
    domain = AgentDomain.CAPSTONE
    description = "Provides guidance for the Autonomous Humanoid capstone project including pipeline setup and troubleshooting"

    # Keywords that trigger this agent
    keywords = [
        # Project terms
        "capstone", "project", "humanoid", "autonomous humanoid",
        "final project", "integration",
        # Pipeline stages
        "pipeline", "voice command", "Whisper", "speech to text",
        "path planning", "navigation", "Nav2", "navigation stack",
        "object recognition", "detection", "manipulation", "grasp",
        # Milestone terms
        "milestone", "progress", "step", "stage", "phase",
        # Troubleshooting
        "not working", "error", "issue", "problem", "debug",
        "troubleshoot", "help with", "stuck",
        # Integration
        "connect", "integrate", "link", "combine"
    ]

    system_prompt = CAPSTONE_SYSTEM_PROMPT

    def __init__(
        self,
        rag_skill: RAGSkill,
        citation_skill: CitationSkill,
        context_skill: ContextSkill,
    ):
        """
        Initialize the capstone agent with required skills.

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
            "temperature": 0.4,
            "max_tokens": 2000,
            "streaming": True,
        }
        if settings.LLM_BASE_URL:
            llm_kwargs["openai_api_base"] = settings.LLM_BASE_URL

        self.llm = ChatOpenAI(**llm_kwargs)

    def can_handle(self, query: str) -> float:
        """
        Return confidence score for handling this query.

        Boosts score for capstone/project patterns.
        """
        base_score = super().can_handle(query)
        query_lower = query.lower()

        # Strong boost for capstone-specific patterns
        capstone_phrases = [
            "capstone", "final project", "autonomous humanoid",
            "project milestone", "pipeline", "voice command navigation",
            "whisper to nav", "path planning"
        ]
        for phrase in capstone_phrases:
            if phrase in query_lower:
                base_score += 0.4
                break

        # Moderate boost for integration/troubleshooting
        integration_terms = [
            "connect", "integrate", "not working", "troubleshoot",
            "how do i", "step by step"
        ]
        if any(term in query_lower for term in integration_terms):
            base_score += 0.15

        return min(base_score, 1.0)

    async def run(
        self,
        query: str,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Run the capstone agent and return complete response.

        Args:
            query: The user's capstone question
            context: Agent context with session info

        Returns:
            AgentResponse with guidance and citations
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
        Run the capstone agent and stream the response.

        Args:
            query: The user's capstone question
            context: Agent context with session info

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        logger.info(f"CapstoneAgent processing: {query[:100]}...")

        try:
            # Detect pipeline stage if applicable
            stage = self._detect_pipeline_stage(query)

            # Retrieve relevant content
            retrieved_content = self.rag_skill.retrieve(
                query=query,
                domain_filter="capstone",
                limit=6,
            )

            # If no capstone-specific content, try general retrieval
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

            # Build query context
            stage_hint = f"\n[Pipeline Stage Detected: {stage}]" if stage else ""

            # Add current query with context
            user_message = f"""Context from the book:
{context_text}
{stage_hint}

User Question: {query}

Please provide practical, implementation-focused guidance for the capstone project. Include code snippets when helpful, and reference which modules contain prerequisite knowledge. Always cite sources using [Source N] format."""

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
            logger.error(f"Error in CapstoneAgent: {e}")
            yield ("text", f"Sorry, an error occurred while processing your capstone question: {str(e)}")
            yield ("end", "")

    def _detect_pipeline_stage(self, query: str) -> str:
        """
        Detect which pipeline stage the query relates to.

        Args:
            query: The user's question

        Returns:
            Pipeline stage name or empty string
        """
        query_lower = query.lower()

        stage_keywords = {
            "voice_command": ["voice", "whisper", "speech", "audio", "microphone"],
            "path_planning": ["path", "planning", "route", "waypoint"],
            "navigation": ["navigation", "nav2", "move", "navigate", "locomotion"],
            "recognition": ["recognition", "detection", "identify", "find", "locate", "vision"],
            "manipulation": ["manipulation", "grasp", "grab", "pick", "arm", "gripper"],
        }

        for stage, keywords in stage_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return stage

        return ""

    def get_milestone_info(self, milestone_id: str) -> Dict[str, Any]:
        """
        Get information about a specific milestone.

        Args:
            milestone_id: Milestone identifier (M1-M6)

        Returns:
            Milestone information dictionary
        """
        milestones = {
            "M1": {
                "name": "Whisper Integration",
                "description": "Integrate Whisper for speech-to-text with ROS 2 topic publishing",
                "prerequisites": ["ROS 2 basics", "Python audio processing"],
                "outputs": ["Voice command topic publishing"],
            },
            "M2": {
                "name": "Path Planning",
                "description": "Create path planner that receives voice commands and generates waypoints",
                "prerequisites": ["M1", "Nav2 basics"],
                "outputs": ["Waypoint list from voice command"],
            },
            "M3": {
                "name": "Navigation",
                "description": "Implement Nav2 navigation to execute movement to waypoints",
                "prerequisites": ["M2", "Nav2 setup", "TF transforms"],
                "outputs": ["Robot movement to goals"],
            },
            "M4": {
                "name": "Object Detection",
                "description": "Setup object detection pipeline for target identification",
                "prerequisites": ["Isaac perception or CV setup"],
                "outputs": ["Object locations in robot frame"],
            },
            "M5": {
                "name": "Manipulation",
                "description": "Control manipulation arm to grasp and interact with objects",
                "prerequisites": ["M4", "MoveIt or Isaac manipulation"],
                "outputs": ["Successful object manipulation"],
            },
            "M6": {
                "name": "Full Integration",
                "description": "Integrate all stages into complete pipeline",
                "prerequisites": ["M1-M5 complete"],
                "outputs": ["End-to-end voice command execution"],
            },
        }
        return milestones.get(milestone_id, {})
