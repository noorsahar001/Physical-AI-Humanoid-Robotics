"""
Agent registry and exports for the subagent architecture.
Constitution v2.0.0: Principle XIII (Agent Scalability)
"""

from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentDomain
from app.agents.router import (
    QueryRouter,
    RouteResult,
    AgentRegistry,
    MultiAgentCoordinator,
    MultiAgentResult,
)

# Import specific agents (will be populated as they are implemented)
# from app.agents.glossary_agent import GlossaryAgent
# from app.agents.hardware_agent import HardwareAgent
# from app.agents.module_info_agent import ModuleInfoAgent
# from app.agents.capstone_agent import CapstoneAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentResponse",
    "AgentDomain",
    "QueryRouter",
    "RouteResult",
    "AgentRegistry",
    "MultiAgentCoordinator",
    "MultiAgentResult",
]


def register_all_agents(
    qdrant_service,
    embedding_service,
    db_service=None,
) -> int:
    """
    Register all available agents with the AgentRegistry.

    Args:
        qdrant_service: QdrantService instance for vector operations
        embedding_service: EmbeddingService for generating embeddings
        db_service: Optional DatabaseService for session management

    Returns:
        Number of agents registered
    """
    import logging
    logger = logging.getLogger(__name__)

    # Import skills
    from app.skills.rag_skill import RAGSkill
    from app.skills.citation_skill import CitationSkill
    from app.skills.context_skill import ContextSkill

    # Create shared skill instances
    rag_skill = RAGSkill(qdrant_service, embedding_service)
    citation_skill = CitationSkill()
    context_skill = ContextSkill(db_service)

    # Clear existing registrations
    AgentRegistry.clear()

    # Register BookAgent as the default/fallback
    from app.agents.book_agent import BookAgent
    book_agent = BookAgentWrapper(
        name="book",
        qdrant_service=qdrant_service,
        embedding_service=embedding_service,
    )
    AgentRegistry.register(book_agent)
    AgentRegistry.set_default("book")

    # Try to register GlossaryAgent
    try:
        from app.agents.glossary_agent import GlossaryAgent
        glossary_agent = GlossaryAgent(
            rag_skill=rag_skill,
            citation_skill=citation_skill,
            context_skill=context_skill,
        )
        AgentRegistry.register(glossary_agent)
    except ImportError:
        logger.info("GlossaryAgent not available")

    # Try to register HardwareAgent
    try:
        from app.agents.hardware_agent import HardwareAgent
        hardware_agent = HardwareAgent(
            rag_skill=rag_skill,
            citation_skill=citation_skill,
            context_skill=context_skill,
        )
        AgentRegistry.register(hardware_agent)
    except ImportError:
        logger.info("HardwareAgent not available")

    # Try to register ModuleInfoAgent
    try:
        from app.agents.module_info_agent import ModuleInfoAgent
        module_info_agent = ModuleInfoAgent(
            rag_skill=rag_skill,
            citation_skill=citation_skill,
            context_skill=context_skill,
        )
        AgentRegistry.register(module_info_agent)
    except ImportError:
        logger.info("ModuleInfoAgent not available")

    # Try to register CapstoneAgent
    try:
        from app.agents.capstone_agent import CapstoneAgent
        capstone_agent = CapstoneAgent(
            rag_skill=rag_skill,
            citation_skill=citation_skill,
            context_skill=context_skill,
        )
        AgentRegistry.register(capstone_agent)
    except ImportError:
        logger.info("CapstoneAgent not available")

    logger.info(f"Registered {AgentRegistry.agent_count()} agents")
    return AgentRegistry.agent_count()


class BookAgentWrapper(BaseAgent):
    """
    Wrapper around the existing BookAgent to make it compatible with BaseAgent interface.
    This allows the BookAgent to be registered in the AgentRegistry.
    """

    name = "book"
    domain = AgentDomain.BOOK
    keywords = [
        "book", "chapter", "content", "page", "section",
        "physical ai", "humanoid", "robotics"
    ]
    system_prompt = "General book content assistant"
    description = "General assistant for all book content (fallback agent)"

    def __init__(
        self,
        name: str,
        qdrant_service,
        embedding_service,
    ):
        from app.agents.book_agent import BookAgent
        self._book_agent = BookAgent(qdrant_service, embedding_service)
        self.name = name

    async def run(self, query: str, context: AgentContext) -> AgentResponse:
        """Run the book agent and return response."""
        result = await self._book_agent.run(
            query=query,
            chat_history=context.chat_history,
            selected_text=context.selected_text,
        )
        return AgentResponse(
            response=result.get("response", ""),
            sources=result.get("sources", []),
            agent_name=self.name,
            confidence=1.0,
        )

    async def run_stream(self, query: str, context: AgentContext):
        """Run the book agent and stream response."""
        async for chunk_type, content in self._book_agent.run_stream(
            query=query,
            chat_history=context.chat_history,
            selected_text=context.selected_text,
        ):
            yield (chunk_type, content)
