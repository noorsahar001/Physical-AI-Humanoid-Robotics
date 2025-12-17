"""
Database service for Neon Serverless Postgres operations.
Handles session management and message storage.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service class for Neon Postgres database operations."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish connection pool to the database."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                settings.NEON_DATABASE_URL,
                min_size=1,
                max_size=10,
            )
            await self._initialize_tables()
            logger.info("Database connection pool established")

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    async def _initialize_tables(self) -> None:
        """Create tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Create sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Create messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    selected_text TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    raw_query TEXT
                )
            """)

            # Create index for faster lookup by session
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)
            """)

            logger.info("Database tables initialized")

    async def create_session(self) -> Dict[str, Any]:
        """Create a new chat session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO sessions DEFAULT VALUES
                RETURNING id, created_at, updated_at
            """)
            logger.info(f"Created new session: {row['id']}")
            return dict(row)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, created_at, updated_at FROM sessions WHERE id = $1",
                UUID(session_id),
            )
            return dict(row) if row else None

    async def update_session_timestamp(self, session_id: str) -> None:
        """Update the session's updated_at timestamp."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE sessions SET updated_at = NOW() WHERE id = $1",
                UUID(session_id),
            )

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        selected_text: Optional[str] = None,
        raw_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a message to a session."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (session_id, role, content, selected_text, raw_query)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, session_id, role, content, selected_text, timestamp, raw_query
                """,
                UUID(session_id),
                role,
                content,
                selected_text,
                raw_query,
            )
            # Update session timestamp
            await self.update_session_timestamp(session_id)
            logger.info(f"Added message to session {session_id}: role={role}")
            return dict(row)

    async def get_session_messages(
        self, session_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get messages for a session, ordered by timestamp."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, session_id, role, content, selected_text, timestamp, raw_query
                FROM messages
                WHERE session_id = $1
                ORDER BY timestamp ASC
                LIMIT $2
                """,
                UUID(session_id),
                limit,
            )
            return [dict(row) for row in rows]


# Global database service instance
_db_service: Optional[DatabaseService] = None


async def get_db_service() -> DatabaseService:
    """Get or create the database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.connect()
    return _db_service


async def close_db_service() -> None:
    """Close the database service."""
    global _db_service
    if _db_service:
        await _db_service.disconnect()
        _db_service = None
