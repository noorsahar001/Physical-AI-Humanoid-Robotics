"""
Agent management API routes.
Constitution v2.0.0: Subagent endpoints for discovery, routing, and direct chat.
"""

from fastapi import APIRouter, HTTPException
from uuid import uuid4
import logging

from app.models.schemas import (
    AgentListResponse,
    AgentDetailResponse,
    AgentSummary,
    RouteRequest,
    RouteResponse,
    AgentChatRequest,
    AgentChatResponse,
    MultiAgentResponse,
    Citation,
)
from app.agents import AgentRegistry, QueryRouter, AgentContext, MultiAgentCoordinator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/agents", response_model=AgentListResponse)
async def list_agents():
    """
    List all registered agents.

    Returns summary information for each available agent including
    name, domain, description, and trigger keywords.
    """
    agents_data = AgentRegistry.list_agents()
    agents = [
        AgentSummary(
            name=a["name"],
            domain=a["domain"],
            description=a["description"],
            keywords=a["keywords"][:10],  # Limit keywords in response
        )
        for a in agents_data
    ]

    return AgentListResponse(
        agents=agents,
        total=len(agents),
    )


@router.get("/agents/{agent_name}", response_model=AgentDetailResponse)
async def get_agent(agent_name: str):
    """
    Get details for a specific agent.

    Args:
        agent_name: The unique name of the agent

    Returns:
        Detailed information about the agent

    Raises:
        404: If the agent is not found
    """
    agent = AgentRegistry.get_agent(agent_name)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found"
        )

    return AgentDetailResponse(
        name=agent.name,
        domain=agent.domain.value if hasattr(agent.domain, 'value') else str(agent.domain),
        description=agent.description,
        keywords=agent.keywords[:20],  # Limit keywords
        is_available=True,
    )


@router.post("/agents/{agent_name}/chat", response_model=AgentChatResponse)
async def chat_with_agent(agent_name: str, request: AgentChatRequest):
    """
    Chat directly with a specific agent.

    Bypasses automatic routing and sends the query directly to the
    specified agent. Useful for testing or when the user wants to
    explicitly choose an agent.

    Args:
        agent_name: The agent to use
        request: Chat request with query and optional context

    Returns:
        Agent response with citations

    Raises:
        404: If the agent is not found
    """
    agent = AgentRegistry.get_agent(agent_name)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found"
        )

    # Create session ID if not provided
    session_id = request.session_id or str(uuid4())

    # Create agent context
    context = AgentContext(
        session_id=session_id,
        query=request.query,
        chat_history=[],
        selected_text=request.selected_text,
    )

    try:
        # Run the agent
        response = await agent.run(request.query, context)

        # Convert sources to citations
        citations = []
        for i, source in enumerate(response.sources, 1):
            citations.append(Citation(
                index=i,
                source=source.get("source", ""),
                title=source.get("title", ""),
                section=source.get("section"),
                relevance_score=source.get("relevance_score", source.get("score")),
            ))

        return AgentChatResponse(
            answer=response.response,
            citations=citations,
            agent_name=response.agent_name,
            confidence=response.confidence,
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Error chatting with agent {agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/route", response_model=RouteResponse)
async def preview_route(request: RouteRequest):
    """
    Preview routing decision for a query.

    Returns which agent would handle the query and the routing
    confidence without actually executing the query. Useful for
    debugging and understanding routing behavior.

    Args:
        request: Query to route

    Returns:
        Routing decision with confidence and reasoning
    """
    router_instance = QueryRouter(AgentRegistry)
    result = router_instance.route(request.query)

    return RouteResponse(
        primary_agent=result.primary_agent,
        secondary_agents=result.secondary_agents,
        confidence=result.confidence,
        reason=result.routing_reason,
        is_multi_domain=result.is_multi_domain,
    )


@router.post("/agents/multi-chat", response_model=MultiAgentResponse)
async def multi_agent_chat(request: AgentChatRequest):
    """
    Handle a query using multi-agent coordination.

    Automatically detects if the query spans multiple domains and
    coordinates responses from relevant agents. Returns a synthesized
    response combining perspectives from all contributing agents.

    Args:
        request: Chat request with query and optional context

    Returns:
        Synthesized response from multiple agents with combined citations
    """
    # Create session ID if not provided
    session_id = request.session_id or str(uuid4())

    # Create agent context
    context = AgentContext(
        session_id=session_id,
        query=request.query,
        chat_history=[],
        selected_text=request.selected_text,
    )

    try:
        # Use multi-agent coordinator
        coordinator = MultiAgentCoordinator(AgentRegistry)
        result = await coordinator.handle_query(
            query=request.query,
            context=context,
            parallel=True,
        )

        # Convert sources to citations
        citations = []
        for i, source in enumerate(result.sources, 1):
            citations.append(Citation(
                index=i,
                source=source.get("source", ""),
                title=source.get("title", ""),
                section=source.get("section"),
                relevance_score=source.get("relevance_score", source.get("score")),
            ))

        return MultiAgentResponse(
            answer=result.response,
            citations=citations,
            agents_used=result.agents_used,
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Error in multi-agent chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing multi-agent request: {str(e)}"
        )


@router.get("/agents/status/summary")
async def agent_status_summary():
    """
    Get a summary of agent status for health monitoring.

    Returns:
        Dictionary with agent count and availability status
    """
    agents = AgentRegistry.all_agents()
    return {
        "total_agents": len(agents),
        "agents": [
            {
                "name": agent.name,
                "domain": agent.domain.value if hasattr(agent.domain, 'value') else str(agent.domain),
                "status": "available",
            }
            for agent in agents
        ],
        "default_agent": AgentRegistry._default_agent,
    }
