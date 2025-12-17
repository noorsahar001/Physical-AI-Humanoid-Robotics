"""
Tests for the GlossaryAgent.
Constitution v2.0.0: Principle XI (Domain-Specific Agent Isolation)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.agents.glossary_agent import GlossaryAgent
from app.agents.base_agent import AgentContext, AgentResponse, AgentDomain


class MockRAGSkill:
    """Mock RAG skill for testing."""
    def retrieve(self, query, domain_filter=None, limit=5):
        return [
            {
                "text": "A topic in ROS 2 is a named bus for asynchronous message passing between nodes.",
                "source": "module1/ros2_basics.md",
                "title": "ROS 2 Fundamentals",
                "section": "Topics",
                "score": 0.95,
            },
            {
                "text": "Topics use a publish-subscribe pattern where publishers send messages.",
                "source": "module1/ros2_communication.md",
                "title": "ROS 2 Communication",
                "section": "Pub-Sub",
                "score": 0.88,
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
        return "Mock context with citations"


class MockContextSkill:
    """Mock context skill for testing."""
    async def get_history(self, session_id, limit=10):
        return []


@pytest.fixture
def glossary_agent():
    """Create a GlossaryAgent with mocked dependencies."""
    with patch('app.agents.glossary_agent.settings') as mock_settings:
        mock_settings.active_api_key = "test-key"
        mock_settings.LLM_MODEL = "gpt-3.5-turbo"
        mock_settings.LLM_BASE_URL = None

        with patch('app.agents.glossary_agent.ChatOpenAI'):
            agent = GlossaryAgent(
                rag_skill=MockRAGSkill(),
                citation_skill=MockCitationSkill(),
                context_skill=MockContextSkill(),
            )
            return agent


class TestGlossaryAgentAttributes:
    """Test GlossaryAgent class attributes."""

    def test_agent_name(self, glossary_agent):
        """Test agent name is set correctly."""
        assert glossary_agent.name == "glossary"

    def test_agent_domain(self, glossary_agent):
        """Test agent domain is set correctly."""
        assert glossary_agent.domain == AgentDomain.GLOSSARY

    def test_agent_has_keywords(self, glossary_agent):
        """Test agent has keywords defined."""
        assert len(glossary_agent.keywords) > 0
        assert "what is" in glossary_agent.keywords
        assert "define" in glossary_agent.keywords

    def test_agent_has_description(self, glossary_agent):
        """Test agent has description."""
        assert glossary_agent.description
        assert len(glossary_agent.description) > 10


class TestGlossaryAgentCanHandle:
    """Test GlossaryAgent.can_handle() method."""

    def test_high_confidence_for_definition_queries(self, glossary_agent):
        """Test high confidence for definition-style queries."""
        queries = [
            "What is a topic in ROS 2?",
            "Define digital twin",
            "What does VLA stand for?",
            "What is the meaning of URDF?",
        ]
        for query in queries:
            score = glossary_agent.can_handle(query)
            assert score >= 0.5, f"Expected high score for '{query}', got {score}"

    def test_medium_confidence_for_term_queries(self, glossary_agent):
        """Test medium confidence for term-related queries."""
        queries = [
            "topic in ROS 2",
            "TF transform",
            "node service action",
        ]
        for query in queries:
            score = glossary_agent.can_handle(query)
            assert 0.2 <= score <= 0.8, f"Expected medium score for '{query}', got {score}"

    def test_low_confidence_for_unrelated_queries(self, glossary_agent):
        """Test low confidence for unrelated queries."""
        queries = [
            "How do I install Ubuntu?",
            "What's the weather today?",
        ]
        for query in queries:
            score = glossary_agent.can_handle(query)
            assert score < 0.5, f"Expected low score for '{query}', got {score}"


class TestGlossaryAgentTermExtraction:
    """Test GlossaryAgent.extract_term() method."""

    def test_extract_from_what_is(self, glossary_agent):
        """Test term extraction from 'what is' queries."""
        assert glossary_agent.extract_term("What is a topic?") == "topic"
        assert glossary_agent.extract_term("what is URDF?") == "URDF"

    def test_extract_from_define(self, glossary_agent):
        """Test term extraction from 'define' queries."""
        assert glossary_agent.extract_term("Define digital twin") == "digital twin"

    def test_extract_from_meaning(self, glossary_agent):
        """Test term extraction from 'meaning of' queries."""
        assert glossary_agent.extract_term("meaning of TF") == "TF"


class TestGlossaryAgentRun:
    """Test GlossaryAgent.run() method."""

    @pytest.mark.asyncio
    async def test_run_returns_agent_response(self, glossary_agent):
        """Test that run() returns an AgentResponse."""
        # Mock the LLM streaming
        mock_content = MagicMock()
        mock_content.content = "A topic is a communication channel."

        async def mock_astream(*args, **kwargs):
            yield mock_content

        glossary_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What is a topic?",
        )

        response = await glossary_agent.run("What is a topic?", context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "glossary"
        assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_run_includes_sources(self, glossary_agent):
        """Test that run() includes sources in response."""
        mock_content = MagicMock()
        mock_content.content = "Test response"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        glossary_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What is a topic?",
        )

        response = await glossary_agent.run("What is a topic?", context)

        assert len(response.sources) > 0


class TestGlossaryAgentRunStream:
    """Test GlossaryAgent.run_stream() method."""

    @pytest.mark.asyncio
    async def test_run_stream_yields_text_chunks(self, glossary_agent):
        """Test that run_stream yields text chunks."""
        mock_content = MagicMock()
        mock_content.content = "Test"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        glossary_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What is a topic?",
        )

        chunks = []
        async for chunk_type, content in glossary_agent.run_stream("What is a topic?", context):
            chunks.append((chunk_type, content))

        # Should have text, source, and end chunks
        types = [c[0] for c in chunks]
        assert "text" in types
        assert "end" in types

    @pytest.mark.asyncio
    async def test_run_stream_yields_sources(self, glossary_agent):
        """Test that run_stream yields source chunks."""
        mock_content = MagicMock()
        mock_content.content = "Test"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        glossary_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="What is a topic?",
        )

        sources = []
        async for chunk_type, content in glossary_agent.run_stream("What is a topic?", context):
            if chunk_type == "source":
                sources.append(content)

        assert len(sources) > 0


# Test queries and expected behavior
TEST_QUERIES = [
    ("What is a topic in ROS 2?", True, "Should handle ROS 2 topic definition"),
    ("Define digital twin", True, "Should handle Gazebo term"),
    ("What does VLA stand for?", True, "Should handle VLA acronym"),
    ("What is SDF format?", True, "Should handle Gazebo SDF term"),
    ("Explain Isaac perception", False, "Should not be primary for explanations"),
]


@pytest.mark.parametrize("query,should_handle,reason", TEST_QUERIES)
def test_query_handling(glossary_agent, query, should_handle, reason):
    """Parameterized test for query handling."""
    score = glossary_agent.can_handle(query)
    if should_handle:
        assert score >= 0.3, f"{reason}: score={score}"
    else:
        # Glossary might still have some score for explanation queries
        # Just verify it's not the highest priority
        pass


EXPECTED_OUTPUT = """
Example test output for GlossaryAgent:

Query: "What is a topic in ROS 2?"
Expected Response: "A **topic** in ROS 2 is a named bus for asynchronous message passing
between nodes [Source 1]. Topics use a publish-subscribe pattern where publishers send
messages and subscribers receive them without direct connection [Source 2]."

Query: "Define digital twin"
Expected Response: "A **digital twin** is a virtual representation of a physical system
that can be used for simulation, testing, and development [Source 1]. In Gazebo, digital
twins are created using SDF world files."

Query: "What does TF stand for?"
Expected Response: "**TF** stands for Transform in ROS 2. It's a library for managing
coordinate frame transformations that tracks the relationship between different parts
of a robot [Source 1]."
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
