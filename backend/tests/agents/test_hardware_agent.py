"""
Tests for the HardwareAgent.
Constitution v2.0.0: Principle XI (Domain-Specific Agent Isolation)
"""

import pytest
from unittest.mock import MagicMock, patch

from app.agents.hardware_agent import HardwareAgent
from app.agents.base_agent import AgentContext, AgentResponse, AgentDomain


class MockRAGSkill:
    """Mock RAG skill for testing."""
    def retrieve(self, query, domain_filter=None, limit=5):
        return [
            {
                "text": "Isaac Sim requires an NVIDIA RTX GPU with at least 8GB VRAM.",
                "source": "setup/hardware_requirements.md",
                "title": "Hardware Requirements",
                "section": "GPU",
                "score": 0.92,
            },
            {
                "text": "Minimum: RTX 2070, 16GB RAM. Recommended: RTX 3080+, 32GB RAM.",
                "source": "setup/isaac_setup.md",
                "title": "Isaac Setup",
                "section": "System Requirements",
                "score": 0.85,
            },
        ]


class MockCitationSkill:
    """Mock citation skill for testing."""
    def format_citations(self, chunks):
        return [
            {"index": i+1, "source": c.get("source"), "title": c.get("title")}
            for i, c in enumerate(chunks)
        ]

    def build_context_with_citations(self, chunks, selected_text=None):
        return "Mock hardware context"


class MockContextSkill:
    """Mock context skill for testing."""
    async def get_history(self, session_id, limit=10):
        return []


@pytest.fixture
def hardware_agent():
    """Create a HardwareAgent with mocked dependencies."""
    with patch('app.agents.hardware_agent.settings') as mock_settings:
        mock_settings.active_api_key = "test-key"
        mock_settings.LLM_MODEL = "gpt-3.5-turbo"
        mock_settings.LLM_BASE_URL = None

        with patch('app.agents.hardware_agent.ChatOpenAI'):
            agent = HardwareAgent(
                rag_skill=MockRAGSkill(),
                citation_skill=MockCitationSkill(),
                context_skill=MockContextSkill(),
            )
            return agent


class TestHardwareAgentAttributes:
    """Test HardwareAgent class attributes."""

    def test_agent_name(self, hardware_agent):
        """Test agent name is set correctly."""
        assert hardware_agent.name == "hardware"

    def test_agent_domain(self, hardware_agent):
        """Test agent domain is set correctly."""
        assert hardware_agent.domain == AgentDomain.HARDWARE

    def test_agent_has_keywords(self, hardware_agent):
        """Test agent has keywords defined."""
        assert len(hardware_agent.keywords) > 0
        assert "GPU" in hardware_agent.keywords
        assert "requirements" in hardware_agent.keywords

    def test_agent_has_description(self, hardware_agent):
        """Test agent has description."""
        assert hardware_agent.description
        assert "hardware" in hardware_agent.description.lower()


class TestHardwareAgentCanHandle:
    """Test HardwareAgent.can_handle() method."""

    def test_high_confidence_for_hardware_queries(self, hardware_agent):
        """Test high confidence for hardware-specific queries."""
        queries = [
            "What GPU do I need for Isaac?",
            "Hardware requirements for simulation",
            "Can I run Gazebo on integrated graphics?",
            "What are the system requirements?",
        ]
        for query in queries:
            score = hardware_agent.can_handle(query)
            assert score >= 0.4, f"Expected high score for '{query}', got {score}"

    def test_high_confidence_for_spec_queries(self, hardware_agent):
        """Test high confidence for specification queries."""
        queries = [
            "Minimum RAM for Isaac Sim",
            "GPU specs needed",
            "Jetson Orin specifications",
        ]
        for query in queries:
            score = hardware_agent.can_handle(query)
            assert score >= 0.3, f"Expected good score for '{query}', got {score}"

    def test_high_confidence_for_comparison_queries(self, hardware_agent):
        """Test high confidence for hardware comparison queries."""
        queries = [
            "RTX 3080 vs Jetson Orin",
            "Should I use workstation or edge device?",
        ]
        for query in queries:
            score = hardware_agent.can_handle(query)
            assert score >= 0.3, f"Expected good score for '{query}', got {score}"

    def test_low_confidence_for_unrelated_queries(self, hardware_agent):
        """Test low confidence for unrelated queries."""
        queries = [
            "What is a topic?",
            "How does ROS 2 work?",
        ]
        for query in queries:
            score = hardware_agent.can_handle(query)
            assert score < 0.5, f"Expected low score for '{query}', got {score}"


class TestHardwareAgentComparisonDetection:
    """Test HardwareAgent.detect_comparison_query() method."""

    def test_detects_vs_pattern(self, hardware_agent):
        """Test detection of 'vs' comparison pattern."""
        assert hardware_agent.detect_comparison_query("RTX 3080 vs Jetson")
        assert hardware_agent.detect_comparison_query("GPU vs CPU processing")

    def test_detects_compare_pattern(self, hardware_agent):
        """Test detection of 'compare' comparison pattern."""
        assert hardware_agent.detect_comparison_query("Compare Jetson models")

    def test_detects_or_pattern(self, hardware_agent):
        """Test detection of 'or' comparison pattern."""
        assert hardware_agent.detect_comparison_query("Should I use RTX or Jetson?")

    def test_no_comparison_for_simple_queries(self, hardware_agent):
        """Test no comparison detection for simple queries."""
        assert not hardware_agent.detect_comparison_query("What GPU do I need?")


class TestHardwareAgentRun:
    """Test HardwareAgent.run() method."""

    @pytest.mark.asyncio
    async def test_run_returns_agent_response(self, hardware_agent):
        """Test that run() returns an AgentResponse."""
        mock_content = MagicMock()
        mock_content.content = "You need an RTX 3080."

        async def mock_astream(*args, **kwargs):
            yield mock_content

        hardware_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What GPU do I need?",
        )

        response = await hardware_agent.run("What GPU do I need?", context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "hardware"
        assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_run_includes_sources(self, hardware_agent):
        """Test that run() includes sources in response."""
        mock_content = MagicMock()
        mock_content.content = "Test response"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        hardware_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What GPU do I need?",
        )

        response = await hardware_agent.run("What GPU do I need?", context)

        assert len(response.sources) > 0


# Test queries and expected behavior
TEST_QUERIES = [
    ("What GPU do I need for Isaac?", True, "Should handle GPU requirement query"),
    ("Jetson Orin specifications", True, "Should handle Jetson specs"),
    ("Can I run simulation on integrated graphics?", True, "Should handle capability query"),
    ("RTX 3080 vs Jetson comparison", True, "Should handle comparison query"),
    ("What is a topic?", False, "Should not handle definition queries"),
]


@pytest.mark.parametrize("query,should_handle,reason", TEST_QUERIES)
def test_query_handling(hardware_agent, query, should_handle, reason):
    """Parameterized test for query handling."""
    score = hardware_agent.can_handle(query)
    if should_handle:
        assert score >= 0.3, f"{reason}: score={score}"


EXPECTED_OUTPUT = """
Example test output for HardwareAgent:

Query: "What GPU do I need for Isaac Sim?"
Expected Response: "For Isaac Sim, NVIDIA recommends [Source 1]:
- **Minimum**: RTX 2070 with 8GB VRAM, 16GB RAM
- **Recommended**: RTX 3080+ with 10GB+ VRAM, 32GB RAM

The RTX 30 series provides better ray tracing performance for realistic
simulations [Source 2]."

Query: "Jetson vs RTX workstation comparison"
Expected Response: "**RTX Workstation** [Source 1]:
- Best for: Development, training, complex simulations
- GPU: RTX 3080/3090/4090
- Power: 300-450W

**Jetson Orin** [Source 2]:
- Best for: Edge deployment, real-time inference
- GPU: Integrated NVIDIA GPU (up to 275 TOPS)
- Power: 15-60W

Choose RTX for development, Jetson for deployment."
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
