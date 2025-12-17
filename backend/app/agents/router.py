"""
Query Router for subagent delegation.
Constitution v2.0.0: Principle XII (Seamless Query Delegation)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
import re
import asyncio

if TYPE_CHECKING:
    from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """Result of routing decision."""
    primary_agent: str
    confidence: float
    routing_reason: str
    secondary_agents: List[str] = field(default_factory=list)
    is_multi_domain: bool = False

    def __post_init__(self):
        """Validate fields."""
        if not 0.0 <= self.confidence <= 1.0:
            self.confidence = max(0.0, min(1.0, self.confidence))


class QueryRouter:
    """
    Routes queries to appropriate subagents.

    Uses a two-phase routing strategy:
    1. Fast path: Keyword matching for high-confidence domain signals
    2. Fallback: Intent classification for ambiguous queries
    """

    # Minimum confidence threshold for routing
    CONFIDENCE_THRESHOLD = 0.3

    # Intent patterns for classification
    DEFINITION_PATTERNS = [
        r'\bwhat is\b', r'\bdefine\b', r'\bmeaning of\b',
        r'\bwhat does .* mean\b', r'\bwhat are\b', r'\bwhat\'s\b'
    ]

    EXPLANATION_PATTERNS = [
        r'\bhow does\b', r'\bhow do\b', r'\bexplain\b',
        r'\bwhy does\b', r'\bwhat happens when\b', r'\bhow to\b'
    ]

    HARDWARE_PATTERNS = [
        r'\brequirements?\b', r'\bspecs?\b', r'\bspecifications?\b',
        r'\bhow much\b', r'\bwhat hardware\b', r'\bcan i run\b',
        r'\bgpu\b', r'\bram\b', r'\bcpu\b', r'\bmemory\b'
    ]

    GUIDANCE_PATTERNS = [
        r'\bproject\b', r'\bmilestone\b', r'\bsteps?\b',
        r'\bpipeline\b', r'\bhow do i\b', r'\btroubleshoot\b'
    ]

    def __init__(self, registry: "AgentRegistry"):
        """
        Initialize the router with an agent registry.

        Args:
            registry: AgentRegistry instance containing registered agents
        """
        self.registry = registry

    def route(self, query: str) -> RouteResult:
        """
        Determine which agent(s) should handle the query.

        Args:
            query: The user's query text

        Returns:
            RouteResult with primary agent, confidence, and optional secondary agents
        """
        logger.info(f"Routing query: {query[:100]}...")

        # Get all registered agents
        agents = self.registry.all_agents()
        if not agents:
            logger.warning("No agents registered, falling back to book agent")
            return RouteResult(
                primary_agent="book",
                confidence=0.0,
                routing_reason="No agents registered"
            )

        # Phase 1: Keyword matching - get confidence scores from each agent
        scores: Dict[str, float] = {}
        for agent in agents:
            score = agent.can_handle(query)
            scores[agent.name] = score
            logger.debug(f"Agent '{agent.name}' scored {score:.2f} for query")

        # Sort by score descending
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Check if best match exceeds threshold
        if sorted_agents and sorted_agents[0][1] >= self.CONFIDENCE_THRESHOLD:
            primary_name, primary_score = sorted_agents[0]

            # Check for secondary agents (multi-domain)
            secondary = [
                name for name, score in sorted_agents[1:3]
                if score >= self.CONFIDENCE_THRESHOLD
            ]

            is_multi = len(secondary) > 0 and sorted_agents[1][1] > 0.4

            logger.info(
                f"Routed to '{primary_name}' with confidence {primary_score:.2f}"
            )

            return RouteResult(
                primary_agent=primary_name,
                confidence=primary_score,
                routing_reason=f"Keyword match: {primary_name} scored {primary_score:.2f}",
                secondary_agents=secondary,
                is_multi_domain=is_multi
            )

        # Phase 2: Intent classification fallback
        intent = self._classify_intent(query)
        intent_agent = self._intent_to_agent(intent)

        logger.info(f"Intent fallback: classified as '{intent}' -> agent '{intent_agent}'")

        return RouteResult(
            primary_agent=intent_agent,
            confidence=0.5 if intent_agent != "book" else 0.0,
            routing_reason=f"Intent classification: {intent}",
            is_multi_domain=False
        )

    def _classify_intent(self, query: str) -> str:
        """
        Classify the query intent based on patterns.

        Args:
            query: The user's query text

        Returns:
            Intent classification: "definition", "explanation", "hardware", "guidance", or "general"
        """
        query_lower = query.lower()

        # Check each intent pattern
        if any(re.search(p, query_lower) for p in self.DEFINITION_PATTERNS):
            return "definition"

        if any(re.search(p, query_lower) for p in self.HARDWARE_PATTERNS):
            return "hardware"

        if any(re.search(p, query_lower) for p in self.GUIDANCE_PATTERNS):
            return "guidance"

        if any(re.search(p, query_lower) for p in self.EXPLANATION_PATTERNS):
            return "explanation"

        return "general"

    def _intent_to_agent(self, intent: str) -> str:
        """
        Map intent classification to agent name.

        Args:
            intent: The classified intent

        Returns:
            Agent name to handle the intent
        """
        intent_mapping = {
            "definition": "glossary",
            "hardware": "hardware",
            "guidance": "capstone",
            "explanation": "module_info",
            "general": "book"
        }
        return intent_mapping.get(intent, "book")

    def preview_route(self, query: str) -> Dict[str, Any]:
        """
        Preview routing decision without executing.

        Args:
            query: The user's query text

        Returns:
            Dictionary with routing details for debugging/preview
        """
        result = self.route(query)

        # Get agent details
        primary_agent = self.registry.get_agent(result.primary_agent)
        secondary_details = []
        for name in result.secondary_agents:
            agent = self.registry.get_agent(name)
            if agent:
                secondary_details.append({
                    "name": name,
                    "domain": agent.domain.value if hasattr(agent.domain, 'value') else str(agent.domain),
                    "description": agent.description
                })

        return {
            "query": query,
            "primary_agent": result.primary_agent,
            "primary_agent_details": {
                "domain": primary_agent.domain.value if primary_agent and hasattr(primary_agent.domain, 'value') else None,
                "description": primary_agent.description if primary_agent else None,
            } if primary_agent else None,
            "secondary_agents": secondary_details,
            "confidence": result.confidence,
            "routing_reason": result.routing_reason,
            "is_multi_domain": result.is_multi_domain,
        }


class AgentRegistry:
    """
    Central registry for agent discovery and management.

    Provides registration, lookup, and enumeration of available agents.
    """

    _agents: Dict[str, "BaseAgent"] = {}
    _default_agent: str = "book"

    @classmethod
    def register(cls, agent: "BaseAgent") -> None:
        """
        Register an agent.

        Args:
            agent: The agent instance to register
        """
        cls._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name} (domain: {agent.domain})")

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Remove an agent from registry.

        Args:
            name: The agent name to unregister
        """
        if name in cls._agents:
            del cls._agents[name]
            logger.info(f"Unregistered agent: {name}")

    @classmethod
    def get_agent(cls, name: str) -> Optional["BaseAgent"]:
        """
        Get agent by name.

        Args:
            name: The agent name to look up

        Returns:
            Agent instance or None if not found
        """
        return cls._agents.get(name)

    @classmethod
    def all_agents(cls) -> List["BaseAgent"]:
        """
        Get all registered agents.

        Returns:
            List of all registered agent instances
        """
        return list(cls._agents.values())

    @classmethod
    def default_agent(cls) -> Optional["BaseAgent"]:
        """
        Get the fallback agent.

        Returns:
            The default agent instance or None
        """
        return cls._agents.get(cls._default_agent)

    @classmethod
    def set_default(cls, name: str) -> None:
        """
        Set the default fallback agent.

        Args:
            name: The agent name to set as default
        """
        if name in cls._agents:
            cls._default_agent = name
            logger.info(f"Set default agent to: {name}")

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents."""
        cls._agents.clear()
        logger.info("Cleared all registered agents")

    @classmethod
    def agent_count(cls) -> int:
        """Get the number of registered agents."""
        return len(cls._agents)

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        """
        List all registered agents with their details.

        Returns:
            List of agent summary dictionaries
        """
        agents_list = []
        for agent in cls._agents.values():
            agents_list.append({
                "name": agent.name,
                "domain": agent.domain.value if hasattr(agent.domain, 'value') else str(agent.domain),
                "description": agent.description,
                "keywords": agent.keywords[:10] if hasattr(agent, 'keywords') else [],
            })
        return agents_list


@dataclass
class MultiAgentResult:
    """Result from multi-agent coordination."""
    response: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    agents_used: List[str] = field(default_factory=list)
    confidence: float = 1.0
    is_synthesized: bool = False


class MultiAgentCoordinator:
    """
    Coordinates execution of multiple agents for cross-domain queries.

    Constitution v2.0.0: Handles queries that require knowledge from
    multiple domains (e.g., "hardware requirements for Isaac Gym simulations").
    """

    # Threshold for considering secondary agents
    SECONDARY_THRESHOLD = 0.4

    # Maximum number of agents to coordinate
    MAX_AGENTS = 3

    def __init__(self, registry: "AgentRegistry"):
        """
        Initialize the coordinator.

        Args:
            registry: AgentRegistry instance with registered agents
        """
        self.registry = registry
        self.router = QueryRouter(registry)

    def detect_multi_domain(self, query: str) -> RouteResult:
        """
        Detect if a query spans multiple domains.

        Uses enhanced detection logic beyond basic routing to identify
        queries that benefit from multiple agent perspectives.

        Args:
            query: The user's query text

        Returns:
            RouteResult with multi-domain information
        """
        route_result = self.router.route(query)

        # Enhanced multi-domain detection
        if not route_result.is_multi_domain:
            # Check for explicit cross-domain patterns
            cross_domain_patterns = [
                # Hardware + Module combinations
                r'\b(requirements?|specs?|hardware)\b.*\b(gazebo|isaac|ros|simulation)',
                r'\b(gazebo|isaac|ros|simulation)\b.*\b(requirements?|specs?|hardware)',
                # Module + Capstone combinations
                r'\b(capstone|project|autonomous)\b.*\b(ros|gazebo|isaac|vla)',
                r'\b(ros|gazebo|isaac|vla)\b.*\b(capstone|project|autonomous)',
                # Multiple modules mentioned
                r'\b(ros|ros2)\b.*\b(gazebo|isaac)',
                r'\b(gazebo)\b.*\b(isaac)',
                # Hardware + Glossary
                r'\b(what is|define)\b.*\b(gpu|jetson|rtx)',
            ]

            query_lower = query.lower()
            for pattern in cross_domain_patterns:
                if re.search(pattern, query_lower):
                    # Re-evaluate secondary agents with lower threshold
                    agents = self.registry.all_agents()
                    scores = {agent.name: agent.can_handle(query) for agent in agents}
                    sorted_agents = sorted(
                        scores.items(), key=lambda x: x[1], reverse=True
                    )

                    # Find secondary agents above threshold
                    secondary = [
                        name for name, score in sorted_agents[1:self.MAX_AGENTS]
                        if score >= 0.3 and name != route_result.primary_agent
                    ]

                    if secondary:
                        logger.info(
                            f"Enhanced multi-domain detection found secondary agents: {secondary}"
                        )
                        return RouteResult(
                            primary_agent=route_result.primary_agent,
                            confidence=route_result.confidence,
                            routing_reason=f"Multi-domain query detected: {pattern}",
                            secondary_agents=secondary,
                            is_multi_domain=True,
                        )
                    break

        return route_result

    async def execute_sequential(
        self,
        query: str,
        context: "AgentContext",
        route_result: RouteResult,
    ) -> List["AgentResponse"]:
        """
        Execute agents sequentially for multi-domain queries.

        Runs primary agent first, then secondary agents in order.
        Each agent receives the original query and context.

        Args:
            query: The user's query
            context: Agent context with session info
            route_result: Routing decision with primary and secondary agents

        Returns:
            List of AgentResponse from each agent
        """
        responses = []

        # Get all agents to execute
        agent_names = [route_result.primary_agent] + route_result.secondary_agents[:self.MAX_AGENTS - 1]

        for agent_name in agent_names:
            agent = self.registry.get_agent(agent_name)
            if not agent:
                logger.warning(f"Agent '{agent_name}' not found, skipping")
                continue

            try:
                logger.info(f"Executing agent '{agent_name}' for multi-domain query")
                response = await agent.run(query, context)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error executing agent '{agent_name}': {e}")
                # Continue with other agents even if one fails

        return responses

    async def execute_parallel(
        self,
        query: str,
        context: "AgentContext",
        route_result: RouteResult,
    ) -> List["AgentResponse"]:
        """
        Execute agents in parallel for multi-domain queries.

        Runs all agents concurrently for faster response times.
        Use when agents are independent and don't need sequential context.

        Args:
            query: The user's query
            context: Agent context with session info
            route_result: Routing decision with primary and secondary agents

        Returns:
            List of AgentResponse from each agent (primary first)
        """
        # Get all agents to execute
        agent_names = [route_result.primary_agent] + route_result.secondary_agents[:self.MAX_AGENTS - 1]

        async def run_agent(agent_name: str) -> Optional["AgentResponse"]:
            agent = self.registry.get_agent(agent_name)
            if not agent:
                logger.warning(f"Agent '{agent_name}' not found, skipping")
                return None

            try:
                logger.info(f"Executing agent '{agent_name}' in parallel")
                return await agent.run(query, context)
            except Exception as e:
                logger.error(f"Error executing agent '{agent_name}': {e}")
                return None

        # Execute all agents in parallel
        tasks = [run_agent(name) for name in agent_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_names[i]} raised exception: {result}")
            elif result is not None:
                responses.append(result)

        return responses

    def synthesize_responses(
        self,
        responses: List["AgentResponse"],
        query: str,
    ) -> MultiAgentResult:
        """
        Synthesize responses from multiple agents into a coherent answer.

        Combines responses intelligently, avoiding redundancy and
        ensuring citations from all sources are preserved.

        Args:
            responses: List of AgentResponse from different agents
            query: Original query for context

        Returns:
            MultiAgentResult with synthesized response
        """
        if not responses:
            return MultiAgentResult(
                response="I couldn't find relevant information to answer your question.",
                sources=[],
                agents_used=[],
                confidence=0.0,
                is_synthesized=False,
            )

        if len(responses) == 1:
            # Single response, no synthesis needed
            resp = responses[0]
            return MultiAgentResult(
                response=resp.response,
                sources=resp.sources,
                agents_used=[resp.agent_name],
                confidence=resp.confidence,
                is_synthesized=False,
            )

        # Multiple responses - synthesize
        agents_used = [r.agent_name for r in responses]
        all_sources = []
        response_parts = []

        # Deduplicate and renumber sources
        source_index = 1
        source_map = {}  # Old source ref -> new source ref

        for i, resp in enumerate(responses):
            agent_name = resp.agent_name.replace("_", " ").title()

            # Add agent section header
            if i == 0:
                response_parts.append(f"**{agent_name} Perspective:**\n{resp.response}")
            else:
                response_parts.append(f"\n\n**{agent_name} Perspective:**\n{resp.response}")

            # Process sources
            for source in resp.sources:
                # Check for duplicate sources
                source_key = (
                    source.get("source", ""),
                    source.get("title", ""),
                    source.get("section", ""),
                )
                if source_key not in source_map:
                    source_map[source_key] = source_index
                    all_sources.append({
                        **source,
                        "contributing_agent": resp.agent_name,
                    })
                    source_index += 1

        # Build synthesized response
        synthesized = "\n".join(response_parts)

        # Calculate combined confidence (average)
        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        logger.info(
            f"Synthesized {len(responses)} responses from agents: {agents_used}"
        )

        return MultiAgentResult(
            response=synthesized,
            sources=all_sources,
            agents_used=agents_used,
            confidence=avg_confidence,
            is_synthesized=True,
        )

    async def handle_query(
        self,
        query: str,
        context: "AgentContext",
        parallel: bool = True,
    ) -> MultiAgentResult:
        """
        Main entry point for handling queries with multi-agent coordination.

        Detects if multi-domain, executes appropriate agents, and
        synthesizes the response. Includes graceful fallback handling.

        Args:
            query: The user's query
            context: Agent context with session info
            parallel: Whether to execute agents in parallel (default True)

        Returns:
            MultiAgentResult with final synthesized response
        """
        import time
        start_time = time.time()

        try:
            # Detect if this is a multi-domain query
            route_result = self.detect_multi_domain(query)

            logger.info(
                f"Multi-agent handling: primary={route_result.primary_agent}, "
                f"secondary={route_result.secondary_agents}, "
                f"is_multi_domain={route_result.is_multi_domain}"
            )

            responses = []

            # Execute agents
            if route_result.is_multi_domain and route_result.secondary_agents:
                execution_mode = "parallel" if parallel else "sequential"
                logger.debug(f"Executing multi-agent query in {execution_mode} mode")

                if parallel:
                    responses = await self.execute_parallel(query, context, route_result)
                else:
                    responses = await self.execute_sequential(query, context, route_result)
            else:
                # Single agent query
                agent = self.registry.get_agent(route_result.primary_agent)
                if agent:
                    try:
                        logger.debug(f"Executing single agent: {route_result.primary_agent}")
                        response = await agent.run(query, context)
                        responses = [response]
                    except Exception as e:
                        logger.error(
                            f"Error executing primary agent '{route_result.primary_agent}': {e}",
                            exc_info=True
                        )
                        # Try fallback to default agent
                        responses = await self._try_fallback(query, context)
                else:
                    logger.warning(
                        f"Primary agent '{route_result.primary_agent}' not found, "
                        "attempting fallback"
                    )
                    responses = await self._try_fallback(query, context)

            # Synthesize and return
            result = self.synthesize_responses(responses, query)

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Multi-agent query completed in {elapsed_ms}ms, "
                f"agents_used={result.agents_used}, "
                f"confidence={result.confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Unexpected error in handle_query: {e}", exc_info=True)
            return MultiAgentResult(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                sources=[],
                agents_used=[],
                confidence=0.0,
                is_synthesized=False,
            )

    async def _try_fallback(
        self,
        query: str,
        context: "AgentContext",
    ) -> List["AgentResponse"]:
        """
        Try to use the fallback/default agent when primary fails.

        Args:
            query: The user's query
            context: Agent context

        Returns:
            List with fallback response or empty list
        """
        default_agent = self.registry.default_agent()
        if default_agent:
            try:
                logger.info(f"Using fallback agent: {default_agent.name}")
                response = await default_agent.run(query, context)
                return [response]
            except Exception as e:
                logger.error(f"Fallback agent also failed: {e}", exc_info=True)

        return []
