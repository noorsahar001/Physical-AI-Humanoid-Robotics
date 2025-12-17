"""
Context Skill for session and conversation history management.
Constitution v2.0.0: Shared skill for all subagents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextSkill:
    """
    Skill for managing conversation context and session history.

    Provides session history retrieval and message management.
    Can be injected into any agent that needs context awareness.
    """

    def __init__(self, db_service=None):
        """
        Initialize the context skill.

        Args:
            db_service: Optional DatabaseService instance for persistent storage
        """
        self.db_service = db_service
        self._local_cache: Dict[str, List[Dict[str, Any]]] = {}

    async def get_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.

        Args:
            session_id: The session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with role and content
        """
        # Try database first if available
        if self.db_service:
            try:
                messages = await self.db_service.get_session_messages(
                    session_id, limit=limit
                )
                return [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages
                ]
            except Exception as e:
                logger.warning(f"Could not retrieve history from DB: {e}")

        # Fallback to local cache
        if session_id in self._local_cache:
            return self._local_cache[session_id][-limit:]

        return []

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save a message to conversation history.

        Args:
            session_id: The session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            agent_name: Optional agent that generated the response
            metadata: Optional additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        # Save to database if available
        if self.db_service:
            try:
                await self.db_service.save_message(session_id, message)
            except Exception as e:
                logger.warning(f"Could not save message to DB: {e}")

        # Also save to local cache
        if session_id not in self._local_cache:
            self._local_cache[session_id] = []
        self._local_cache[session_id].append(message)

        # Limit cache size per session
        if len(self._local_cache[session_id]) > 100:
            self._local_cache[session_id] = self._local_cache[session_id][-50:]

        logger.debug(f"ContextSkill saved message for session {session_id}")

    def format_history_for_llm(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Format conversation history for LLM context.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted string suitable for LLM context
        """
        if not messages:
            return ""

        formatted_parts = ["Previous conversation:"]
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            formatted_parts.append(f"{role}: {content}")

        return "\n".join(formatted_parts)

    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a session.

        Args:
            session_id: The session identifier to clear
        """
        if session_id in self._local_cache:
            del self._local_cache[session_id]
        logger.info(f"ContextSkill cleared session {session_id}")

    def get_last_agent(self, session_id: str) -> Optional[str]:
        """
        Get the last agent that responded in a session.

        Args:
            session_id: The session identifier

        Returns:
            Agent name or None if no previous response
        """
        if session_id in self._local_cache:
            for msg in reversed(self._local_cache[session_id]):
                if msg.get("role") == "assistant" and msg.get("agent_name"):
                    return msg["agent_name"]
        return None
