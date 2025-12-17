"""
Chat API routes for the RAG Chatbot.
Constitution v2.0.0: Provides streaming chat endpoint with subagent routing.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import logging
import time
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    Citation,
    EmbedRequest,
    EmbedResponse,
    ErrorResponse,
    RouteRequest,
    RouteResponse,
)
from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.agents.book_agent import BookAgent
from app.agents import AgentRegistry, QueryRouter, AgentContext, MultiAgentCoordinator

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session storage for multi-turn conversations (US4)
# Structure: {session_id: {"messages": [...], "last_activity": datetime}}
_sessions: Dict[str, Dict[str, Any]] = {}

# Session timeout in minutes (T045: 30 min inactive cleanup)
SESSION_TIMEOUT_MINUTES = 30


def _cleanup_stale_sessions() -> int:
    """Remove sessions that have been inactive for more than SESSION_TIMEOUT_MINUTES.

    Returns:
        Number of sessions cleaned up
    """
    global _sessions
    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    stale_sessions = [
        sid for sid, session in _sessions.items()
        if session.get("last_activity", datetime.min) < cutoff
    ]

    for sid in stale_sessions:
        del _sessions[sid]

    if stale_sessions:
        logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")

    return len(stale_sessions)


def _get_or_create_session(session_id: str = None) -> tuple:
    """Get existing session or create new one.

    Also performs cleanup of stale sessions.
    """
    # Periodically cleanup stale sessions (every call with some probability or threshold)
    if len(_sessions) > 100:  # Only cleanup if we have many sessions
        _cleanup_stale_sessions()

    current_time = datetime.utcnow()

    if session_id and session_id in _sessions:
        # Update last activity
        _sessions[session_id]["last_activity"] = current_time
        return session_id, _sessions[session_id]

    # Create new session
    new_session_id = str(uuid4())
    _sessions[new_session_id] = {
        "messages": [],
        "last_activity": current_time,
        "created_at": current_time,
    }
    return new_session_id, _sessions[new_session_id]


def _validate_query(query: str) -> tuple:
    """Validate query and return (is_valid, error_message)."""
    if not query or not query.strip():
        return False, "Query cannot be empty"

    if len(query) > 2000:
        return False, "Query exceeds maximum length of 2000 characters"

    # Check if query is only special characters
    if not any(c.isalnum() for c in query):
        return False, "Query must contain at least one alphanumeric character"

    return True, None


def _get_router() -> QueryRouter:
    """Get a QueryRouter instance."""
    return QueryRouter(AgentRegistry)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and receive a complete response.

    Returns the full answer with citations after processing is complete.
    Now includes agent attribution and multi-agent coordination (Constitution v2.0.0).
    """
    start_time = time.time()

    # Validate query
    is_valid, error_msg = _validate_query(request.query)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Get or create session
    session_id, session = _get_or_create_session(request.session_id)

    # Get services
    embedding_service = get_embedding_service()
    qdrant_service = get_qdrant_service()

    # Use multi-agent coordinator to detect and handle cross-domain queries
    coordinator = MultiAgentCoordinator(AgentRegistry)
    route_result = coordinator.detect_multi_domain(request.query)
    logger.info(
        f"Routed to '{route_result.primary_agent}' "
        f"(confidence: {route_result.confidence:.2f}, "
        f"multi_domain: {route_result.is_multi_domain})"
    )

    try:
        context = AgentContext(
            session_id=session_id,
            query=request.query,
            chat_history=session["messages"],
            selected_text=request.selected_text,
        )

        # Handle multi-domain queries with coordinator
        if route_result.is_multi_domain and route_result.secondary_agents:
            logger.info(f"Using multi-agent coordination with secondary agents: {route_result.secondary_agents}")
            result = await coordinator.handle_query(request.query, context, parallel=True)

            # Store messages in session
            session["messages"].append({"role": "user", "content": request.query})
            session["messages"].append({"role": "assistant", "content": result.response})

            # Build citations from sources
            citations = []
            for i, source in enumerate(result.sources, 1):
                if isinstance(source, dict):
                    citations.append(Citation(
                        index=i,
                        source=source.get("source", ""),
                        title=source.get("title", ""),
                        section=source.get("section"),
                        relevance_score=source.get("relevance_score", source.get("score")),
                    ))

            latency_ms = int((time.time() - start_time) * 1000)

            return ChatResponse(
                answer=result.response,
                citations=citations,
                query_id=str(uuid4()),
                session_id=session_id,
                latency_ms=latency_ms,
                agent_used=result.agents_used[0] if result.agents_used else "book",
                routing_confidence=result.confidence,
                agents_used=result.agents_used,
                is_multi_agent=result.is_synthesized,
            )

        # Single agent query - use appropriate agent
        agent = AgentRegistry.get_agent(route_result.primary_agent)

        if agent and route_result.primary_agent != "book":
            # Use subagent
            response = await agent.run(request.query, context)

            # Store messages in session
            session["messages"].append({"role": "user", "content": request.query})
            session["messages"].append({"role": "assistant", "content": response.response})

            # Build citations from sources
            citations = []
            for i, source in enumerate(response.sources, 1):
                if isinstance(source, dict):
                    citations.append(Citation(
                        index=source.get("index", i),
                        source=source.get("source", ""),
                        title=source.get("title", ""),
                        section=source.get("section"),
                        relevance_score=source.get("relevance_score", source.get("score")),
                    ))

            latency_ms = int((time.time() - start_time) * 1000)

            return ChatResponse(
                answer=response.response,
                citations=citations,
                query_id=str(uuid4()),
                session_id=session_id,
                latency_ms=latency_ms,
                agent_used=response.agent_name,
                routing_confidence=route_result.confidence,
                agents_used=[response.agent_name],
                is_multi_agent=False,
            )
        else:
            # Fallback to BookAgent
            book_agent = BookAgent(qdrant_service, embedding_service)
            result = await book_agent.run(
                query=request.query,
                chat_history=session["messages"],
                selected_text=request.selected_text,
            )

            # Store messages in session
            session["messages"].append({"role": "user", "content": request.query})
            session["messages"].append({"role": "assistant", "content": result["response"]})

            # Build citations
            citations = []
            for source in result.get("sources", []):
                if isinstance(source, dict):
                    citations.append(Citation(**source))

            latency_ms = int((time.time() - start_time) * 1000)

            return ChatResponse(
                answer=result["response"],
                citations=citations,
                query_id=str(uuid4()),
                session_id=session_id,
                latency_ms=latency_ms,
                agent_used="book",
                routing_confidence=route_result.confidence,
                agents_used=["book"],
                is_multi_agent=False,
            )

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a chat response based on the user's query.

    The response is sent as Server-Sent Events (SSE) with the following event types:
    - text: Streamed response text chunks
    - citation: Citation information (JSON)
    - done: End of stream signal
    - error: Error message if something goes wrong

    Now includes agent attribution in chunks (Constitution v2.0.0).
    """
    # Validate query
    is_valid, error_msg = _validate_query(request.query)
    if not is_valid:
        async def error_generator():
            error_chunk = ChatStreamChunk(
                type="error",
                content=error_msg,
                session_id="",
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")

    # Get or create session
    session_id, session = _get_or_create_session(request.session_id)

    # Get services
    embedding_service = get_embedding_service()
    qdrant_service = get_qdrant_service()

    # Route the query (Constitution v2.0.0)
    router_instance = _get_router()
    route_result = router_instance.route(request.query)
    agent = AgentRegistry.get_agent(route_result.primary_agent)
    agent_name = route_result.primary_agent

    async def generate_response():
        """Generator function for streaming response."""
        full_assistant_response = ""
        has_yielded = False

        try:
            if agent and route_result.primary_agent != "book":
                # Use subagent
                context = AgentContext(
                    session_id=session_id,
                    query=request.query,
                    chat_history=session["messages"],
                    selected_text=request.selected_text,
                )
                async for chunk_type, content in agent.run_stream(request.query, context):
                    if chunk_type == "text":
                        has_yielded = True
                        full_assistant_response += content
                        chunk = ChatStreamChunk(
                            type="text",
                            content=content,
                            session_id=session_id,
                            agent_used=agent_name,
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

                    elif chunk_type == "source":
                        chunk = ChatStreamChunk(
                            type="citation",
                            content=json.dumps(content) if isinstance(content, dict) else content,
                            session_id=session_id,
                            agent_used=agent_name,
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

                    elif chunk_type == "end":
                        chunk = ChatStreamChunk(
                            type="done",
                            content="",
                            session_id=session_id,
                            agent_used=agent_name,
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"
            else:
                # Fallback to BookAgent
                book_agent = BookAgent(qdrant_service, embedding_service)
                async for chunk_type, content in book_agent.run_stream(
                    query=request.query,
                    chat_history=session["messages"],
                    selected_text=request.selected_text,
                ):
                    if chunk_type == "text":
                        has_yielded = True
                        full_assistant_response += content
                        chunk = ChatStreamChunk(
                            type="text",
                            content=content,
                            session_id=session_id,
                            agent_used="book",
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

                    elif chunk_type == "source":
                        chunk = ChatStreamChunk(
                            type="citation",
                            content=json.dumps(content) if isinstance(content, dict) else content,
                            session_id=session_id,
                            agent_used="book",
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

                    elif chunk_type == "end":
                        chunk = ChatStreamChunk(
                            type="done",
                            content="",
                            session_id=session_id,
                            agent_used="book",
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

            # Safety fallback: if nothing was yielded, send a fallback message
            if not has_yielded:
                fallback_msg = "I apologize, but I couldn't generate a response. Please try again."
                fallback_chunk = ChatStreamChunk(
                    type="text",
                    content=fallback_msg,
                    session_id=session_id,
                    agent_used="book",
                )
                yield f"data: {fallback_chunk.model_dump_json()}\n\n"
                full_assistant_response = fallback_msg

                done_chunk = ChatStreamChunk(
                    type="done",
                    content="",
                    session_id=session_id,
                    agent_used="book",
                )
                yield f"data: {done_chunk.model_dump_json()}\n\n"

            # Store messages in session
            session["messages"].append({"role": "user", "content": request.query})
            if full_assistant_response:
                session["messages"].append({"role": "assistant", "content": full_assistant_response})

        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_chunk = ChatStreamChunk(
                type="error",
                content=f"An error occurred: {str(e)}",
                session_id=session_id,
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

            end_chunk = ChatStreamChunk(
                type="done",
                content="",
                session_id=session_id,
            )
            yield f"data: {end_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/route", response_model=RouteResponse)
async def preview_chat_route(request: RouteRequest):
    """
    Preview routing decision for a query without executing.

    Useful for debugging and understanding which agent would handle a query.
    """
    router_instance = _get_router()
    result = router_instance.route(request.query)

    return RouteResponse(
        primary_agent=result.primary_agent,
        secondary_agents=result.secondary_agents,
        confidence=result.confidence,
        reason=result.routing_reason,
        is_multi_domain=result.is_multi_domain,
    )


@router.post("/embed", response_model=EmbedResponse)
async def embed_content(request: EmbedRequest):
    """
    Embed new content and store it in the vector database.

    This endpoint is used for manually ingesting new book content (legacy).
    For bulk ingestion, use POST /ingest instead.
    """
    try:
        embedding_service = get_embedding_service()
        qdrant_service = get_qdrant_service()

        # Generate embedding
        embedding = embedding_service.generate_embedding(request.text)

        # Prepare payload
        chunk_id = request.chunk_id or str(uuid4())
        payload = {
            "text": request.text,
            "source": request.source,
            "title": request.page_title,
            "section": "",
            "position": 0,
        }

        # Store in Qdrant
        qdrant_service.upsert_vectors(
            vectors=[embedding],
            payloads=[payload],
            ids=[chunk_id],
        )

        return EmbedResponse(
            success=True,
            chunk_id=chunk_id,
            message=f"Content embedded successfully with ID: {chunk_id}",
        )

    except Exception as e:
        logger.error(f"Error embedding content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to embed content: {str(e)}",
        )


@router.get("/info")
async def get_info():
    """Get information about the chatbot service including registered agents."""
    try:
        qdrant_service = get_qdrant_service()
        collection_info = qdrant_service.get_collection_info()

        # Get agent info (Constitution v2.0.0)
        agents = AgentRegistry.list_agents()

        return {
            "service": "RAG Chatbot",
            "version": "2.0.0",
            "constitution": "v2.0.0",
            "collection": collection_info,
            "agents": {
                "total": len(agents),
                "list": [a["name"] for a in agents],
            },
        }

    except Exception as e:
        logger.error(f"Error getting info: {e}")
        return {
            "service": "RAG Chatbot",
            "version": "2.0.0",
            "constitution": "v2.0.0",
            "collection": {"error": str(e)},
            "agents": {"total": 0, "list": []},
        }
