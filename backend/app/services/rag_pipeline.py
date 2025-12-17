"""
RAG Pipeline orchestrating the entire retrieval-augmented generation flow.
Coordinates embedding, retrieval, context injection, and agent execution.
Constitution v2.0.0: Updated with subagent routing support.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import logging

from app.services.db_service import DatabaseService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.agents.book_agent import BookAgent
from app.agents import AgentRegistry, QueryRouter, AgentContext

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates the RAG pipeline for the chatbot.

    Flow:
    1. Receive user query and optional selected text
    2. Route query to appropriate subagent (Constitution v2.0.0)
    3. Retrieve chat history from database
    4. Generate embeddings for the query
    5. Search Qdrant for relevant content
    6. Inject context into the agent
    7. Stream the agent's response
    """

    def __init__(
        self,
        db_service: DatabaseService,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
    ):
        self.db_service = db_service
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.agent = BookAgent(qdrant_service, embedding_service)
        self.router = QueryRouter(AgentRegistry)

        # Track last routing result for response metadata
        self._last_route_result = None

    async def run_rag_stream(
        self,
        session_id: str,
        query: str,
        selected_text: Optional[str] = None,
    ) -> AsyncGenerator[tuple, None]:
        """
        Run the RAG pipeline and stream the response.

        Args:
            session_id: The chat session ID
            query: The user's question
            selected_text: Optional text selected by the user

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        logger.info(f"Starting RAG pipeline for session {session_id}")

        try:
            # Step 1: Route the query to the appropriate agent
            route_result = self.router.route(query)
            self._last_route_result = route_result
            logger.info(
                f"Routed to '{route_result.primary_agent}' "
                f"(confidence: {route_result.confidence:.2f})"
            )

            # Step 2: Retrieve chat history for context
            chat_history = await self._get_chat_history(session_id)
            logger.info(f"Retrieved {len(chat_history)} messages from history")

            # Step 3: Create agent context
            context = AgentContext(
                session_id=session_id,
                query=query,
                chat_history=chat_history,
                selected_text=selected_text,
            )

            # Step 4: Get the appropriate agent
            agent = AgentRegistry.get_agent(route_result.primary_agent)

            if agent and route_result.primary_agent != "book":
                # Use the specialized subagent
                logger.info(f"Using subagent: {agent.name}")
                async for chunk_type, content in agent.run_stream(query, context):
                    yield (chunk_type, content)
            else:
                # Fallback to BookAgent
                logger.info("Using fallback BookAgent")
                async for chunk_type, content in self.agent.run_stream(
                    query=query,
                    chat_history=chat_history,
                    selected_text=selected_text,
                ):
                    yield (chunk_type, content)

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            yield ("text", f"An error occurred: {str(e)}")
            yield ("end", "")

    async def run_rag(
        self,
        session_id: str,
        query: str,
        selected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the RAG pipeline and return the complete response.

        Args:
            session_id: The chat session ID
            query: The user's question
            selected_text: Optional text selected by the user

        Returns:
            Dictionary with response, sources, and agent info
        """
        full_response = ""
        sources = []

        async for chunk_type, content in self.run_rag_stream(
            session_id, query, selected_text
        ):
            if chunk_type == "text":
                full_response += content
            elif chunk_type == "source":
                sources.append(content)

        result = {
            "response": full_response,
            "sources": sources,
        }

        # Add routing metadata if available
        if self._last_route_result:
            result["agent_used"] = self._last_route_result.primary_agent
            result["routing_confidence"] = self._last_route_result.confidence

        return result

    def get_last_routing_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the last routing decision.

        Returns:
            Dictionary with routing details or None
        """
        if self._last_route_result:
            return {
                "primary_agent": self._last_route_result.primary_agent,
                "confidence": self._last_route_result.confidence,
                "reason": self._last_route_result.routing_reason,
                "is_multi_domain": self._last_route_result.is_multi_domain,
                "secondary_agents": self._last_route_result.secondary_agents,
            }
        return None

    async def _get_chat_history(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get formatted chat history for the agent.

        Args:
            session_id: The session ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with role and content
        """
        try:
            messages = await self.db_service.get_session_messages(
                session_id, limit=limit
            )
            return [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]
        except Exception as e:
            logger.warning(f"Could not retrieve chat history: {e}")
            return []

    async def embed_content(
        self,
        text: str,
        source: str,
        page_title: str,
        chunk_id: Optional[str] = None,
    ) -> str:
        """
        Embed a piece of content and store it in Qdrant.

        Args:
            text: The text content to embed
            source: Source URL or identifier
            page_title: Title of the source page
            chunk_id: Optional unique ID for the chunk

        Returns:
            The chunk ID
        """
        from uuid import uuid4

        # Generate embedding
        embedding = self.embedding_service.generate_embedding(text)

        # Prepare payload
        payload = {
            "text": text,
            "source": source,
            "page_title": page_title,
            "chunk_id": chunk_id or str(uuid4()),
        }

        # Store in Qdrant
        self.qdrant_service.upsert_vectors(
            vectors=[embedding],
            payloads=[payload],
            ids=[payload["chunk_id"]],
        )

        logger.info(f"Embedded content from {source}: {len(text)} chars")
        return payload["chunk_id"]

    def preview_route(self, query: str) -> Dict[str, Any]:
        """
        Preview routing decision without executing the query.

        Args:
            query: The query to route

        Returns:
            Dictionary with routing preview details
        """
        return self.router.preview_route(query)
