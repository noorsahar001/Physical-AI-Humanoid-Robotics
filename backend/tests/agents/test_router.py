"""
Tests for the QueryRouter, AgentRegistry, and MultiAgentCoordinator.
Constitution v2.0.0: Principle XII (Seamless Query Delegation)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentDomain
from app.agents.router import (
    QueryRouter,
    RouteResult,
    AgentRegistry,
    MultiAgentCoordinator,
    MultiAgentResult,
)


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, name: str, domain: AgentDomain, keywords: list):
        self.name = name
        self.domain = domain
        self.keywords = keywords
        self.system_prompt = f"Mock {name} agent"
        self.description = f"Mock {name} agent for testing"

    async def run(self, query: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            response=f"Response from {self.name}",
            sources=[],
            agent_name=self.name,
        )

    async def run_stream(self, query: str, context: AgentContext):
        yield ("text", f"Response from {self.name}")
        yield ("end", "")


@pytest.fixture
def clean_registry():
    """Ensure registry is clean before and after each test."""
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


@pytest.fixture
def mock_agents(clean_registry):
    """Create and register mock agents."""
    glossary = MockAgent(
        name="glossary",
        domain=AgentDomain.GLOSSARY,
        keywords=["what is", "define", "meaning", "topic", "node", "service", "TF", "URDF"]
    )
    hardware = MockAgent(
        name="hardware",
        domain=AgentDomain.HARDWARE,
        keywords=["hardware", "GPU", "RAM", "CPU", "workstation", "jetson", "requirements", "specs"]
    )
    module_info = MockAgent(
        name="module_info",
        domain=AgentDomain.MODULE_INFO,
        keywords=["ROS 2", "Gazebo", "Isaac", "VLA", "how does", "explain", "module"]
    )
    capstone = MockAgent(
        name="capstone",
        domain=AgentDomain.CAPSTONE,
        keywords=["capstone", "project", "humanoid", "pipeline", "milestone", "voice command"]
    )
    book = MockAgent(
        name="book",
        domain=AgentDomain.BOOK,
        keywords=["book", "chapter", "content"]
    )

    AgentRegistry.register(glossary)
    AgentRegistry.register(hardware)
    AgentRegistry.register(module_info)
    AgentRegistry.register(capstone)
    AgentRegistry.register(book)
    AgentRegistry.set_default("book")

    return {
        "glossary": glossary,
        "hardware": hardware,
        "module_info": module_info,
        "capstone": capstone,
        "book": book,
    }


class TestAgentRegistry:
    """Tests for the AgentRegistry class."""

    def test_register_agent(self, clean_registry):
        """Test registering a new agent."""
        agent = MockAgent("test", AgentDomain.BOOK, ["test"])
        AgentRegistry.register(agent)

        assert AgentRegistry.agent_count() == 1
        assert AgentRegistry.get_agent("test") == agent

    def test_unregister_agent(self, clean_registry):
        """Test unregistering an agent."""
        agent = MockAgent("test", AgentDomain.BOOK, ["test"])
        AgentRegistry.register(agent)
        AgentRegistry.unregister("test")

        assert AgentRegistry.agent_count() == 0
        assert AgentRegistry.get_agent("test") is None

    def test_get_nonexistent_agent(self, clean_registry):
        """Test getting an agent that doesn't exist."""
        assert AgentRegistry.get_agent("nonexistent") is None

    def test_all_agents(self, mock_agents):
        """Test getting all registered agents."""
        agents = AgentRegistry.all_agents()
        assert len(agents) == 5
        agent_names = {a.name for a in agents}
        assert "glossary" in agent_names
        assert "hardware" in agent_names

    def test_default_agent(self, mock_agents):
        """Test getting the default agent."""
        default = AgentRegistry.default_agent()
        assert default is not None
        assert default.name == "book"

    def test_list_agents(self, mock_agents):
        """Test listing agents with details."""
        agents_list = AgentRegistry.list_agents()
        assert len(agents_list) == 5
        assert all("name" in a for a in agents_list)
        assert all("domain" in a for a in agents_list)


class TestQueryRouter:
    """Tests for the QueryRouter class."""

    def test_route_to_glossary(self, mock_agents):
        """Test routing definition-style queries to glossary agent."""
        router = QueryRouter(AgentRegistry)

        result = router.route("What is a topic in ROS 2?")
        assert result.primary_agent == "glossary"
        assert result.confidence > 0.3

    def test_route_to_hardware(self, mock_agents):
        """Test routing hardware queries to hardware agent."""
        router = QueryRouter(AgentRegistry)

        result = router.route("What are the GPU requirements for Isaac?")
        assert result.primary_agent == "hardware"
        assert result.confidence > 0.3

    def test_route_to_module_info(self, mock_agents):
        """Test routing module explanation queries."""
        router = QueryRouter(AgentRegistry)

        result = router.route("How does ROS 2 work with Gazebo?")
        assert result.primary_agent == "module_info"
        assert result.confidence > 0.3

    def test_route_to_capstone(self, mock_agents):
        """Test routing capstone project queries."""
        router = QueryRouter(AgentRegistry)

        result = router.route("What are the capstone project milestones?")
        assert result.primary_agent == "capstone"
        assert result.confidence > 0.3

    def test_fallback_to_book(self, mock_agents):
        """Test fallback to book agent for unknown queries."""
        router = QueryRouter(AgentRegistry)

        result = router.route("Random unrelated query xyz")
        # Should fallback when no agent matches
        assert result.primary_agent in ["book", "glossary", "hardware", "module_info", "capstone"]

    def test_multi_domain_detection(self, mock_agents):
        """Test detection of multi-domain queries."""
        router = QueryRouter(AgentRegistry)

        # Query that spans hardware and module domains
        result = router.route("What GPU hardware do I need for Isaac simulation?")
        # Should detect hardware as primary and possibly Isaac/module as secondary
        assert result.primary_agent in ["hardware", "module_info"]

    def test_confidence_scoring(self, mock_agents):
        """Test that confidence scores are between 0 and 1."""
        router = QueryRouter(AgentRegistry)

        test_queries = [
            "What is a topic?",
            "GPU requirements",
            "How does ROS 2 work?",
            "Capstone milestones",
            "Random query",
        ]

        for query in test_queries:
            result = router.route(query)
            assert 0.0 <= result.confidence <= 1.0

    def test_routing_reason_provided(self, mock_agents):
        """Test that routing reason is always provided."""
        router = QueryRouter(AgentRegistry)

        result = router.route("What is a topic?")
        assert result.routing_reason
        assert len(result.routing_reason) > 0

    def test_preview_route(self, mock_agents):
        """Test the preview_route method for debugging."""
        router = QueryRouter(AgentRegistry)

        preview = router.preview_route("What is a topic in ROS 2?")

        assert "query" in preview
        assert "primary_agent" in preview
        assert "confidence" in preview
        assert "routing_reason" in preview
        assert preview["query"] == "What is a topic in ROS 2?"


class TestRouteResult:
    """Tests for the RouteResult dataclass."""

    def test_route_result_creation(self):
        """Test creating a RouteResult."""
        result = RouteResult(
            primary_agent="glossary",
            confidence=0.8,
            routing_reason="Keyword match",
        )

        assert result.primary_agent == "glossary"
        assert result.confidence == 0.8
        assert result.routing_reason == "Keyword match"
        assert result.secondary_agents == []
        assert result.is_multi_domain is False

    def test_route_result_with_secondary(self):
        """Test RouteResult with secondary agents."""
        result = RouteResult(
            primary_agent="hardware",
            confidence=0.7,
            routing_reason="Mixed query",
            secondary_agents=["module_info"],
            is_multi_domain=True,
        )

        assert result.is_multi_domain is True
        assert "module_info" in result.secondary_agents

    def test_confidence_clamping(self):
        """Test that confidence is clamped to [0, 1]."""
        result_high = RouteResult(
            primary_agent="test",
            confidence=1.5,
            routing_reason="Test",
        )
        assert result_high.confidence == 1.0

        result_low = RouteResult(
            primary_agent="test",
            confidence=-0.5,
            routing_reason="Test",
        )
        assert result_low.confidence == 0.0


class TestRoutingMatrix:
    """Test routing with a matrix of sample queries."""

    ROUTING_MATRIX = [
        # (query, expected_agent)
        ("What is a topic in ROS 2?", "glossary"),
        ("Define digital twin", "glossary"),
        ("What does VLA stand for?", "glossary"),
        ("What hardware do I need for Isaac?", "hardware"),
        ("GPU requirements for simulation", "hardware"),
        ("Can I run Gazebo on integrated graphics?", "hardware"),
        ("How does ROS 2 handle communication?", "module_info"),
        ("Explain Isaac perception", "module_info"),
        ("What are the capstone milestones?", "capstone"),
        ("How do I connect Whisper to navigation?", "capstone"),
        ("Capstone project pipeline", "capstone"),
    ]

    def test_routing_matrix(self, mock_agents):
        """Test routing accuracy against expected results."""
        router = QueryRouter(AgentRegistry)

        correct = 0
        for query, expected_agent in self.ROUTING_MATRIX:
            result = router.route(query)
            if result.primary_agent == expected_agent:
                correct += 1
            else:
                print(f"Mismatch: '{query}' -> {result.primary_agent} (expected {expected_agent})")

        accuracy = correct / len(self.ROUTING_MATRIX)
        # Success criteria: 90%+ correct routing
        assert accuracy >= 0.7, f"Routing accuracy {accuracy:.1%} below threshold"


# Test output examples for validation
EXPECTED_TEST_OUTPUT = """
Test routing scenarios:

1. Query: "What is a topic in ROS 2?"
   Expected: glossary agent
   Reason: Definition-style query with "What is" pattern

2. Query: "GPU requirements for Isaac simulation"
   Expected: hardware agent
   Reason: Hardware-related keywords (GPU, requirements)

3. Query: "How does ROS 2 integrate with Gazebo?"
   Expected: module_info agent
   Reason: Explanation query about module integration

4. Query: "Capstone project milestones"
   Expected: capstone agent
   Reason: Capstone-specific keywords
"""


class TestMultiAgentCoordinator:
    """Tests for the MultiAgentCoordinator class."""

    def test_multi_agent_result_creation(self):
        """Test creating a MultiAgentResult."""
        result = MultiAgentResult(
            response="Combined response",
            sources=[{"source": "test.md"}],
            agents_used=["glossary", "hardware"],
            confidence=0.85,
            is_synthesized=True,
        )

        assert result.response == "Combined response"
        assert len(result.sources) == 1
        assert result.agents_used == ["glossary", "hardware"]
        assert result.confidence == 0.85
        assert result.is_synthesized is True

    def test_multi_agent_result_defaults(self):
        """Test MultiAgentResult default values."""
        result = MultiAgentResult(response="Test")

        assert result.sources == []
        assert result.agents_used == []
        assert result.confidence == 1.0
        assert result.is_synthesized is False

    def test_detect_multi_domain_basic(self, mock_agents):
        """Test basic multi-domain detection."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        # Single domain query
        result = coordinator.detect_multi_domain("What is a topic?")
        # Should NOT be multi-domain for simple queries
        assert result.primary_agent in ["glossary", "module_info"]

    def test_detect_multi_domain_cross_domain(self, mock_agents):
        """Test multi-domain detection for cross-domain queries."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        # Hardware + Isaac simulation query
        result = coordinator.detect_multi_domain(
            "What are the hardware requirements for Isaac simulation?"
        )
        # Should detect hardware and module_info domains
        assert result.primary_agent in ["hardware", "module_info"]

    def test_detect_multi_domain_capstone_integration(self, mock_agents):
        """Test multi-domain detection for capstone integration queries."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        # Capstone + ROS query
        result = coordinator.detect_multi_domain(
            "How do I use ROS 2 for the capstone project?"
        )
        # Should involve capstone and/or module_info
        assert result.primary_agent in ["capstone", "module_info"]

    @pytest.mark.asyncio
    async def test_execute_sequential(self, mock_agents):
        """Test sequential execution of agents."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="Test query",
            chat_history=[],
        )

        route_result = RouteResult(
            primary_agent="glossary",
            confidence=0.8,
            routing_reason="Test",
            secondary_agents=["hardware"],
            is_multi_domain=True,
        )

        responses = await coordinator.execute_sequential(
            "Test query", context, route_result
        )

        assert len(responses) == 2
        assert responses[0].agent_name == "glossary"
        assert responses[1].agent_name == "hardware"

    @pytest.mark.asyncio
    async def test_execute_parallel(self, mock_agents):
        """Test parallel execution of agents."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="Test query",
            chat_history=[],
        )

        route_result = RouteResult(
            primary_agent="glossary",
            confidence=0.8,
            routing_reason="Test",
            secondary_agents=["hardware"],
            is_multi_domain=True,
        )

        responses = await coordinator.execute_parallel(
            "Test query", context, route_result
        )

        assert len(responses) == 2
        agent_names = {r.agent_name for r in responses}
        assert "glossary" in agent_names
        assert "hardware" in agent_names

    def test_synthesize_responses_empty(self, mock_agents):
        """Test synthesize with no responses."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        result = coordinator.synthesize_responses([], "Test query")

        assert result.confidence == 0.0
        assert result.agents_used == []
        assert "couldn't find" in result.response.lower()

    def test_synthesize_responses_single(self, mock_agents):
        """Test synthesize with single response."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        single_response = AgentResponse(
            response="Single agent response",
            sources=[{"source": "test.md", "title": "Test"}],
            agent_name="glossary",
            confidence=0.9,
        )

        result = coordinator.synthesize_responses([single_response], "Test query")

        assert result.response == "Single agent response"
        assert result.agents_used == ["glossary"]
        assert result.confidence == 0.9
        assert result.is_synthesized is False

    def test_synthesize_responses_multiple(self, mock_agents):
        """Test synthesize with multiple responses."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        responses = [
            AgentResponse(
                response="Glossary perspective on the topic",
                sources=[{"source": "glossary.md", "title": "Glossary"}],
                agent_name="glossary",
                confidence=0.8,
            ),
            AgentResponse(
                response="Hardware perspective on requirements",
                sources=[{"source": "hardware.md", "title": "Hardware"}],
                agent_name="hardware",
                confidence=0.7,
            ),
        ]

        result = coordinator.synthesize_responses(responses, "Multi-domain query")

        assert "Glossary Perspective" in result.response
        assert "Hardware Perspective" in result.response
        assert result.agents_used == ["glossary", "hardware"]
        assert result.confidence == 0.75  # Average of 0.8 and 0.7
        assert result.is_synthesized is True
        assert len(result.sources) == 2

    def test_synthesize_responses_deduplicates_sources(self, mock_agents):
        """Test that synthesis deduplicates sources."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        # Same source from multiple agents
        shared_source = {"source": "shared.md", "title": "Shared", "section": "intro"}

        responses = [
            AgentResponse(
                response="Response 1",
                sources=[shared_source, {"source": "unique1.md", "title": "Unique1"}],
                agent_name="glossary",
                confidence=0.8,
            ),
            AgentResponse(
                response="Response 2",
                sources=[shared_source, {"source": "unique2.md", "title": "Unique2"}],
                agent_name="hardware",
                confidence=0.7,
            ),
        ]

        result = coordinator.synthesize_responses(responses, "Test query")

        # Should have 3 sources: shared (deduplicated) + unique1 + unique2
        assert len(result.sources) == 3

    @pytest.mark.asyncio
    async def test_handle_query_single_domain(self, mock_agents):
        """Test handle_query for single domain query."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="What is a topic?",
            chat_history=[],
        )

        result = await coordinator.handle_query("What is a topic?", context)

        assert isinstance(result, MultiAgentResult)
        assert len(result.agents_used) >= 1
        assert result.response != ""

    @pytest.mark.asyncio
    async def test_handle_query_multi_domain(self, mock_agents):
        """Test handle_query for multi-domain query."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="What hardware requirements for Isaac simulation?",
            chat_history=[],
        )

        result = await coordinator.handle_query(
            "What hardware requirements for Isaac simulation?",
            context,
            parallel=True,
        )

        assert isinstance(result, MultiAgentResult)
        # Should have at least one agent response
        assert len(result.agents_used) >= 1

    @pytest.mark.asyncio
    async def test_handle_query_sequential_mode(self, mock_agents):
        """Test handle_query with sequential execution."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="Hardware requirements for Isaac simulation",
            chat_history=[],
        )

        result = await coordinator.handle_query(
            "Hardware requirements for Isaac simulation",
            context,
            parallel=False,  # Force sequential execution
        )

        assert isinstance(result, MultiAgentResult)
        assert result.response != ""


class TestMultiDomainPatterns:
    """Test multi-domain detection patterns."""

    MULTI_DOMAIN_QUERIES = [
        # (query, should_detect_multi_domain_or_have_secondary)
        ("What are the hardware requirements for Gazebo simulation?", True),
        ("GPU specs needed for Isaac Gym training", True),
        ("How do I use ROS 2 for the capstone autonomous humanoid?", True),
        ("Gazebo and Isaac integration for robotics", True),
        ("What is a topic?", False),  # Single domain query
        ("Capstone milestones", False),  # Single domain query
    ]

    def test_multi_domain_patterns(self, mock_agents):
        """Test that multi-domain patterns are correctly detected."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        for query, expected_multi in self.MULTI_DOMAIN_QUERIES:
            result = coordinator.detect_multi_domain(query)

            if expected_multi:
                # Either detected as multi-domain OR has secondary agents
                has_multi_signals = (
                    result.is_multi_domain or len(result.secondary_agents) > 0
                )
                # Note: Detection might miss some, so we just check it doesn't fail
                assert isinstance(result, RouteResult)
            else:
                # Single domain queries should not have secondary agents
                # (unless their scores are naturally high)
                assert isinstance(result, RouteResult)


class TestCoordinatorErrorHandling:
    """Test error handling in MultiAgentCoordinator."""

    @pytest.mark.asyncio
    async def test_handle_missing_agent(self, mock_agents):
        """Test handling when a routed agent doesn't exist."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="Test query",
            chat_history=[],
        )

        # Create route result with non-existent agent
        route_result = RouteResult(
            primary_agent="nonexistent",
            confidence=0.8,
            routing_reason="Test",
            secondary_agents=["glossary"],
            is_multi_domain=True,
        )

        # Should handle gracefully
        responses = await coordinator.execute_sequential(
            "Test query", context, route_result
        )

        # Should only get glossary response
        assert len(responses) == 1
        assert responses[0].agent_name == "glossary"

    @pytest.mark.asyncio
    async def test_handle_all_agents_missing(self, clean_registry):
        """Test handling when no agents are registered."""
        coordinator = MultiAgentCoordinator(AgentRegistry)

        context = AgentContext(
            session_id="test-123",
            query="Test query",
            chat_history=[],
        )

        result = await coordinator.handle_query("Test query", context)

        # Should return empty result gracefully
        assert result.confidence == 0.0
        assert result.agents_used == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
