"""
Base Agent abstract class and core data structures for the subagent architecture.
Constitution v2.0.0: Principle X (Modular Subagent Architecture)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncGenerator
from enum import Enum
import re


class AgentDomain(str, Enum):
    """Valid domains for agents and content tagging."""
    GLOSSARY = "glossary"
    HARDWARE = "hardware"
    MODULE_INFO = "module_info"
    CAPSTONE = "capstone"
    BOOK = "book"  # Fallback / general


@dataclass
class AgentContext:
    """Context passed to agents when handling queries."""
    session_id: str
    query: str
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    selected_text: Optional[str] = None
    domain_filter: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate context fields."""
        if not self.session_id:
            self.session_id = "anonymous"
        if len(self.query) > 2000:
            self.query = self.query[:2000]
        # Limit chat history to last 10 messages
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]


@dataclass
class AgentResponse:
    """Standard response structure from any agent."""
    response: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    agent_name: str = "unknown"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate response fields."""
        if not 0.0 <= self.confidence <= 1.0:
            self.confidence = max(0.0, min(1.0, self.confidence))


class BaseAgent(ABC):
    """
    Abstract base class for all domain-specific subagents.

    All subagents must implement:
    - name: Unique agent identifier
    - domain: Domain scope (AgentDomain enum value)
    - keywords: List of keywords that trigger this agent
    - system_prompt: Agent-specific system prompt
    - description: Human-readable description
    - run(): Synchronous execution
    - run_stream(): Streaming execution

    Optionally override:
    - can_handle(): Custom confidence scoring logic
    """

    # Required class attributes (must be set by subclasses)
    name: str
    domain: AgentDomain
    keywords: List[str]
    system_prompt: str
    description: str

    def can_handle(self, query: str) -> float:
        """
        Return confidence score (0-1) for handling this query.

        Default implementation uses keyword matching with pattern detection.
        Override for more sophisticated detection logic.

        Args:
            query: The user's query text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        query_lower = query.lower()

        # Count keyword matches
        keyword_matches = sum(
            1 for kw in self.keywords
            if kw.lower() in query_lower
        )

        # Base score from keyword matches (max 0.6 from keywords alone)
        base_score = min(keyword_matches / 3.0, 0.6)

        # Bonus for definition-style queries (for glossary agent)
        definition_patterns = [
            r'\bwhat is\b', r'\bdefine\b', r'\bmeaning of\b',
            r'\bwhat does .* mean\b', r'\bwhat are\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in definition_patterns):
            if self.domain == AgentDomain.GLOSSARY:
                base_score += 0.3

        # Bonus for explanation-style queries (for module info agent)
        explanation_patterns = [
            r'\bhow does\b', r'\bhow do\b', r'\bexplain\b',
            r'\bwhy does\b', r'\bwhat happens when\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in explanation_patterns):
            if self.domain == AgentDomain.MODULE_INFO:
                base_score += 0.2

        # Bonus for hardware-style queries
        hardware_patterns = [
            r'\brequirements?\b', r'\bspecs?\b', r'\bspecifications?\b',
            r'\bhow much\b', r'\bwhat hardware\b', r'\bcan i run\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in hardware_patterns):
            if self.domain == AgentDomain.HARDWARE:
                base_score += 0.25

        # Bonus for capstone/project queries
        capstone_patterns = [
            r'\bproject\b', r'\bmilestone\b', r'\bstep\b',
            r'\bpipeline\b', r'\bhow do i\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in capstone_patterns):
            if self.domain == AgentDomain.CAPSTONE:
                base_score += 0.2

        return min(base_score, 1.0)

    @abstractmethod
    async def run(
        self,
        query: str,
        context: AgentContext,
    ) -> AgentResponse:
        """
        Run the agent and return complete response.

        Args:
            query: The user's question
            context: AgentContext with session info, history, etc.

        Returns:
            AgentResponse with response text and sources
        """
        pass

    @abstractmethod
    async def run_stream(
        self,
        query: str,
        context: AgentContext,
    ) -> AsyncGenerator[tuple, None]:
        """
        Run the agent and stream the response.

        Args:
            query: The user's question
            context: AgentContext with session info, history, etc.

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, domain={self.domain.value})>"
