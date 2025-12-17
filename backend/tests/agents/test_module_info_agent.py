"""
Tests for the ModuleInfoAgent.
Constitution v2.0.0: Principle XI (Domain-Specific Agent Isolation)
"""

import pytest
from unittest.mock import MagicMock, patch

from app.agents.module_info_agent import ModuleInfoAgent
from app.agents.base_agent import AgentContext, AgentResponse, AgentDomain


class MockRAGSkill:
    """Mock RAG skill for testing."""
    def retrieve(self, query, domain_filter=None, limit=5):
        return [
            {
                "text": "ROS 2 nodes communicate through topics using publish-subscribe pattern.",
                "source": "module1/ros2_communication.md",
                "title": "ROS 2 Communication",
                "section": "Topics",
                "score": 0.90,
            },
            {
                "text": "Services provide synchronous request-response communication.",
                "source": "module1/ros2_services.md",
                "title": "ROS 2 Services",
                "section": "Overview",
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
        return "Mock module context"


class MockContextSkill:
    """Mock context skill for testing."""
    async def get_history(self, session_id, limit=10):
        return []


@pytest.fixture
def module_info_agent():
    """Create a ModuleInfoAgent with mocked dependencies."""
    with patch('app.agents.module_info_agent.settings') as mock_settings:
        mock_settings.active_api_key = "test-key"
        mock_settings.LLM_MODEL = "gpt-3.5-turbo"
        mock_settings.LLM_BASE_URL = None

        with patch('app.agents.module_info_agent.ChatOpenAI'):
            agent = ModuleInfoAgent(
                rag_skill=MockRAGSkill(),
                citation_skill=MockCitationSkill(),
                context_skill=MockContextSkill(),
            )
            return agent


class TestModuleInfoAgentAttributes:
    """Test ModuleInfoAgent class attributes."""

    def test_agent_name(self, module_info_agent):
        """Test agent name is set correctly."""
        assert module_info_agent.name == "module_info"

    def test_agent_domain(self, module_info_agent):
        """Test agent domain is set correctly."""
        assert module_info_agent.domain == AgentDomain.MODULE_INFO

    def test_agent_has_keywords(self, module_info_agent):
        """Test agent has keywords defined."""
        assert len(module_info_agent.keywords) > 0
        assert "how does" in module_info_agent.keywords
        assert "explain" in module_info_agent.keywords
        assert "ROS 2" in module_info_agent.keywords

    def test_agent_has_description(self, module_info_agent):
        """Test agent has description."""
        assert module_info_agent.description
        assert "module" in module_info_agent.description.lower()


class TestModuleInfoAgentCanHandle:
    """Test ModuleInfoAgent.can_handle() method."""

    def test_high_confidence_for_explanation_queries(self, module_info_agent):
        """Test high confidence for explanation-style queries."""
        queries = [
            "How does ROS 2 handle communication?",
            "Explain Isaac perception pipeline",
            "How do topics work in ROS 2?",
            "Walk me through Gazebo setup",
        ]
        for query in queries:
            score = module_info_agent.can_handle(query)
            assert score >= 0.4, f"Expected high score for '{query}', got {score}"

    def test_high_confidence_for_module_queries(self, module_info_agent):
        """Test high confidence for module-specific queries."""
        queries = [
            "ROS 2 node lifecycle",
            "Gazebo physics engine",
            "Isaac Sim perception",
            "VLA model architecture",
        ]
        for query in queries:
            score = module_info_agent.can_handle(query)
            assert score >= 0.3, f"Expected good score for '{query}', got {score}"

    def test_low_confidence_for_definition_queries(self, module_info_agent):
        """Test lower confidence for pure definition queries."""
        queries = [
            "What is a topic?",
            "Define URDF",
        ]
        for query in queries:
            score = module_info_agent.can_handle(query)
            # Should still have some score, but not primary
            assert score < 0.8, f"Expected lower score for '{query}', got {score}"


class TestModuleInfoAgentModuleDetection:
    """Test ModuleInfoAgent._detect_module() method."""

    def test_detects_ros2_module(self, module_info_agent):
        """Test detection of ROS 2 module."""
        assert module_info_agent._detect_module("How do ROS 2 topics work?") == "ros2"
        assert module_info_agent._detect_module("Explain node lifecycle") == "ros2"

    def test_detects_gazebo_module(self, module_info_agent):
        """Test detection of Gazebo module."""
        assert module_info_agent._detect_module("How does Gazebo simulation work?") == "gazebo"
        assert module_info_agent._detect_module("Physics engine configuration") == "gazebo"

    def test_detects_isaac_module(self, module_info_agent):
        """Test detection of Isaac module."""
        assert module_info_agent._detect_module("Isaac Sim perception") == "isaac"
        assert module_info_agent._detect_module("Omniverse setup") == "isaac"

    def test_detects_vla_module(self, module_info_agent):
        """Test detection of VLA module."""
        assert module_info_agent._detect_module("VLA model training") == "vla"
        assert module_info_agent._detect_module("Neural policy learning") == "vla"

    def test_no_module_for_general_query(self, module_info_agent):
        """Test no module detection for general queries."""
        assert module_info_agent._detect_module("General robotics question") == ""


class TestModuleInfoAgentRun:
    """Test ModuleInfoAgent.run() method."""

    @pytest.mark.asyncio
    async def test_run_returns_agent_response(self, module_info_agent):
        """Test that run() returns an AgentResponse."""
        mock_content = MagicMock()
        mock_content.content = "ROS 2 nodes communicate through topics."

        async def mock_astream(*args, **kwargs):
            yield mock_content

        module_info_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="How does ROS 2 communication work?",
        )

        response = await module_info_agent.run("How does ROS 2 communication work?", context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "module_info"
        assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_run_includes_sources(self, module_info_agent):
        """Test that run() includes sources in response."""
        mock_content = MagicMock()
        mock_content.content = "Test response"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        module_info_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="How does ROS 2 work?",
        )

        response = await module_info_agent.run("How does ROS 2 work?", context)

        assert len(response.sources) > 0


# Test queries and expected behavior
TEST_QUERIES = [
    ("How does ROS 2 handle communication?", True, "Should handle ROS 2 explanation"),
    ("Explain Gazebo physics engine", True, "Should handle Gazebo explanation"),
    ("Walk me through Isaac perception", True, "Should handle Isaac explanation"),
    ("How do VLA models work?", True, "Should handle VLA explanation"),
    ("GPU requirements for simulation", False, "Should not be primary for hardware"),
]


@pytest.mark.parametrize("query,should_handle,reason", TEST_QUERIES)
def test_query_handling(module_info_agent, query, should_handle, reason):
    """Parameterized test for query handling."""
    score = module_info_agent.can_handle(query)
    if should_handle:
        assert score >= 0.3, f"{reason}: score={score}"


EXPECTED_OUTPUT = """
Example test output for ModuleInfoAgent:

Query: "How does ROS 2 handle communication?"
Expected Response: "ROS 2 uses several communication patterns [Source 1]:

**Topics** (Publish-Subscribe):
- Asynchronous message passing
- One-to-many communication
```python
self.publisher = self.create_publisher(String, 'topic', 10)
```

**Services** (Request-Response):
- Synchronous communication
- One-to-one pattern [Source 2]

**Actions** (Goal-Feedback-Result):
- For long-running tasks
- Provides feedback during execution"

Query: "Explain Isaac perception pipeline"
Expected Response: "Isaac perception uses a multi-stage pipeline [Source 1]:

1. **Sensor Input**: RGB-D cameras, LiDAR
2. **Object Detection**: Neural network inference
3. **Segmentation**: Instance/semantic segmentation
4. **Pose Estimation**: 6-DOF object poses
5. **Scene Graph**: Spatial relationship modeling

Prerequisites: Module 2 (sensors), Module 3 (Isaac setup)."
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
