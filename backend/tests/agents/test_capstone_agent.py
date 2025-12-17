"""
Tests for the CapstoneAgent.
Constitution v2.0.0: Principle XI (Domain-Specific Agent Isolation)
"""

import pytest
from unittest.mock import MagicMock, patch

from app.agents.capstone_agent import CapstoneAgent
from app.agents.base_agent import AgentContext, AgentResponse, AgentDomain


class MockRAGSkill:
    """Mock RAG skill for testing."""
    def retrieve(self, query, domain_filter=None, limit=5):
        return [
            {
                "text": "The capstone pipeline connects Whisper output to the path planner.",
                "source": "capstone/pipeline.md",
                "title": "Capstone Pipeline",
                "section": "Voice to Navigation",
                "score": 0.92,
            },
            {
                "text": "Milestone M1 involves integrating Whisper with ROS 2 topic publishing.",
                "source": "capstone/milestones.md",
                "title": "Project Milestones",
                "section": "M1",
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
        return "Mock capstone context"


class MockContextSkill:
    """Mock context skill for testing."""
    async def get_history(self, session_id, limit=10):
        return []


@pytest.fixture
def capstone_agent():
    """Create a CapstoneAgent with mocked dependencies."""
    with patch('app.agents.capstone_agent.settings') as mock_settings:
        mock_settings.active_api_key = "test-key"
        mock_settings.LLM_MODEL = "gpt-3.5-turbo"
        mock_settings.LLM_BASE_URL = None

        with patch('app.agents.capstone_agent.ChatOpenAI'):
            agent = CapstoneAgent(
                rag_skill=MockRAGSkill(),
                citation_skill=MockCitationSkill(),
                context_skill=MockContextSkill(),
            )
            return agent


class TestCapstoneAgentAttributes:
    """Test CapstoneAgent class attributes."""

    def test_agent_name(self, capstone_agent):
        """Test agent name is set correctly."""
        assert capstone_agent.name == "capstone"

    def test_agent_domain(self, capstone_agent):
        """Test agent domain is set correctly."""
        assert capstone_agent.domain == AgentDomain.CAPSTONE

    def test_agent_has_keywords(self, capstone_agent):
        """Test agent has keywords defined."""
        assert len(capstone_agent.keywords) > 0
        assert "capstone" in capstone_agent.keywords
        assert "milestone" in capstone_agent.keywords
        assert "pipeline" in capstone_agent.keywords

    def test_agent_has_description(self, capstone_agent):
        """Test agent has description."""
        assert capstone_agent.description
        assert "capstone" in capstone_agent.description.lower()


class TestCapstoneAgentCanHandle:
    """Test CapstoneAgent.can_handle() method."""

    def test_high_confidence_for_capstone_queries(self, capstone_agent):
        """Test high confidence for capstone-specific queries."""
        queries = [
            "What are the capstone milestones?",
            "How do I connect Whisper to navigation?",
            "Capstone project pipeline",
            "Autonomous humanoid project",
        ]
        for query in queries:
            score = capstone_agent.can_handle(query)
            assert score >= 0.4, f"Expected high score for '{query}', got {score}"

    def test_high_confidence_for_pipeline_queries(self, capstone_agent):
        """Test high confidence for pipeline-related queries."""
        queries = [
            "Voice command to navigation flow",
            "Object manipulation pipeline",
            "Path planning integration",
        ]
        for query in queries:
            score = capstone_agent.can_handle(query)
            assert score >= 0.3, f"Expected good score for '{query}', got {score}"

    def test_high_confidence_for_troubleshooting_queries(self, capstone_agent):
        """Test high confidence for troubleshooting queries."""
        queries = [
            "My robot isn't responding to voice commands",
            "Navigation not working in capstone",
            "Troubleshoot manipulation arm",
        ]
        for query in queries:
            score = capstone_agent.can_handle(query)
            assert score >= 0.3, f"Expected good score for '{query}', got {score}"

    def test_low_confidence_for_unrelated_queries(self, capstone_agent):
        """Test low confidence for unrelated queries."""
        queries = [
            "What is a topic?",
            "GPU requirements",
        ]
        for query in queries:
            score = capstone_agent.can_handle(query)
            assert score < 0.5, f"Expected low score for '{query}', got {score}"


class TestCapstoneAgentPipelineStageDetection:
    """Test CapstoneAgent._detect_pipeline_stage() method."""

    def test_detects_voice_command_stage(self, capstone_agent):
        """Test detection of voice command stage."""
        assert capstone_agent._detect_pipeline_stage("Whisper integration") == "voice_command"
        assert capstone_agent._detect_pipeline_stage("Speech to text setup") == "voice_command"

    def test_detects_path_planning_stage(self, capstone_agent):
        """Test detection of path planning stage."""
        assert capstone_agent._detect_pipeline_stage("Path planning from voice") == "path_planning"
        assert capstone_agent._detect_pipeline_stage("Generate waypoints") == "path_planning"

    def test_detects_navigation_stage(self, capstone_agent):
        """Test detection of navigation stage."""
        assert capstone_agent._detect_pipeline_stage("Nav2 navigation") == "navigation"
        assert capstone_agent._detect_pipeline_stage("Robot movement") == "navigation"

    def test_detects_recognition_stage(self, capstone_agent):
        """Test detection of recognition stage."""
        assert capstone_agent._detect_pipeline_stage("Object detection") == "recognition"
        assert capstone_agent._detect_pipeline_stage("Find the cup") == "recognition"

    def test_detects_manipulation_stage(self, capstone_agent):
        """Test detection of manipulation stage."""
        assert capstone_agent._detect_pipeline_stage("Grasp the object") == "manipulation"
        assert capstone_agent._detect_pipeline_stage("Manipulation arm") == "manipulation"

    def test_no_stage_for_general_query(self, capstone_agent):
        """Test no stage detection for general queries."""
        assert capstone_agent._detect_pipeline_stage("Capstone milestones") == ""


class TestCapstoneAgentMilestoneInfo:
    """Test CapstoneAgent.get_milestone_info() method."""

    def test_get_m1_info(self, capstone_agent):
        """Test getting M1 milestone info."""
        info = capstone_agent.get_milestone_info("M1")
        assert info["name"] == "Whisper Integration"
        assert "Whisper" in info["description"]

    def test_get_m6_info(self, capstone_agent):
        """Test getting M6 milestone info."""
        info = capstone_agent.get_milestone_info("M6")
        assert info["name"] == "Full Integration"
        assert "M1-M5" in str(info["prerequisites"])

    def test_get_invalid_milestone(self, capstone_agent):
        """Test getting info for invalid milestone."""
        info = capstone_agent.get_milestone_info("M99")
        assert info == {}


class TestCapstoneAgentRun:
    """Test CapstoneAgent.run() method."""

    @pytest.mark.asyncio
    async def test_run_returns_agent_response(self, capstone_agent):
        """Test that run() returns an AgentResponse."""
        mock_content = MagicMock()
        mock_content.content = "Connect Whisper to ROS 2 topics."

        async def mock_astream(*args, **kwargs):
            yield mock_content

        capstone_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="How do I connect Whisper to navigation?",
        )

        response = await capstone_agent.run("How do I connect Whisper to navigation?", context)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "capstone"
        assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_run_includes_sources(self, capstone_agent):
        """Test that run() includes sources in response."""
        mock_content = MagicMock()
        mock_content.content = "Test response"

        async def mock_astream(*args, **kwargs):
            yield mock_content

        capstone_agent.llm.astream = mock_astream

        context = AgentContext(
            session_id="test-session",
            query="Capstone milestones",
        )

        response = await capstone_agent.run("Capstone milestones", context)

        assert len(response.sources) > 0


# Test queries and expected behavior
TEST_QUERIES = [
    ("What are the capstone milestones?", True, "Should handle milestone query"),
    ("How do I connect Whisper to Nav2?", True, "Should handle integration query"),
    ("My humanoid isn't responding to voice", True, "Should handle troubleshooting"),
    ("Capstone project pipeline overview", True, "Should handle pipeline query"),
    ("What is a topic?", False, "Should not handle definition queries"),
]


@pytest.mark.parametrize("query,should_handle,reason", TEST_QUERIES)
def test_query_handling(capstone_agent, query, should_handle, reason):
    """Parameterized test for query handling."""
    score = capstone_agent.can_handle(query)
    if should_handle:
        assert score >= 0.3, f"{reason}: score={score}"


EXPECTED_OUTPUT = """
Example test output for CapstoneAgent:

Query: "What are the capstone milestones?"
Expected Response: "The Autonomous Humanoid capstone has 6 milestones [Source 1]:

**M1: Whisper Integration**
- Integrate speech-to-text with ROS 2
- Output: Voice commands on `/whisper_text` topic

**M2: Path Planning**
- Convert voice commands to navigation goals
- Output: Waypoint list

**M3: Nav2 Navigation**
- Execute movement to waypoints
- Prerequisites: TF setup, map

**M4: Object Detection**
- Identify target objects
- Output: Object poses

**M5: Manipulation**
- Grasp and interact with objects
- Prerequisites: Arm control setup

**M6: Full Integration**
- End-to-end pipeline working"

Query: "How do I connect Whisper to navigation?"
Expected Response: "To connect Whisper to Nav2 [Source 1]:

**Step 1**: Create a ROS 2 node subscribing to Whisper:
```python
self.whisper_sub = self.create_subscription(
    String, 'whisper_text', self.command_callback, 10)
```

**Step 2**: Parse command and create navigation goal:
```python
def command_callback(self, msg):
    if 'go to' in msg.data:
        goal = self.parse_location(msg.data)
        self.nav_client.send_goal(goal)
```

**Step 3**: Send goal to Nav2 action server [Source 2]."
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
