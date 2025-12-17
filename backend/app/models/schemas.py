"""
Pydantic models for API request and response schemas.
Constitution v2.0.0: Extended with subagent schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# Agent Domain Enum (for API)
class AgentDomainEnum(str, Enum):
    """Valid domains for agents."""
    GLOSSARY = "glossary"
    HARDWARE = "hardware"
    MODULE_INFO = "module_info"
    CAPSTONE = "capstone"
    BOOK = "book"


# Chat Schemas
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., min_length=1, max_length=2000, description="The user's question about the book")
    session_id: Optional[str] = Field(None, description="Optional session ID for multi-turn conversations")
    selected_text: Optional[str] = Field(None, description="Optional text highlighted by the user")


class Citation(BaseModel):
    """Citation reference to source material."""
    index: int = Field(..., ge=1, description="Citation number (1-based)")
    source: str = Field(..., description="File path or URL to source document")
    title: str = Field(..., description="Document title")
    section: Optional[str] = Field(None, description="Section within the document")
    relevance_score: Optional[float] = Field(None, ge=0, le=1, description="Similarity score (0-1)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="The generated answer based on book content")
    citations: List[Citation] = Field(default_factory=list, description="List of source citations")
    query_id: str = Field(..., description="Unique identifier for this query")
    session_id: str = Field(..., description="Session ID for follow-up questions")
    latency_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    # New fields for subagent support (Constitution v2.0.0)
    agent_used: Optional[str] = Field(None, description="Primary agent that handled the query")
    routing_confidence: Optional[float] = Field(None, ge=0, le=1, description="Routing confidence score")
    # Multi-agent coordination fields (Constitution v2.0.0 Phase 8)
    agents_used: List[str] = Field(default_factory=list, description="All agents that contributed to response")
    is_multi_agent: bool = Field(False, description="Whether multiple agents contributed")


class ChatStreamChunk(BaseModel):
    """Response chunk model for streaming chat responses."""
    type: Literal["text", "citation", "done", "error"] = Field(..., description="Type of stream chunk")
    content: str = Field(..., description="Chunk content")
    session_id: str = Field(..., description="The session ID for this conversation")
    agent_used: Optional[str] = Field(None, description="Agent that generated this chunk")


# Ingestion Schemas
class IngestRequest(BaseModel):
    """Request model for ingestion endpoint."""
    docs_path: Optional[str] = Field(None, description="Path to documents folder")
    force_reingest: bool = Field(False, description="Force re-ingestion of all documents")


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint."""
    status: Literal["success", "partial", "failed"] = Field(..., description="Ingestion status")
    documents_processed: int = Field(..., description="Number of documents successfully processed")
    chunks_created: int = Field(..., description="Total chunks created")
    errors: List[str] = Field(default_factory=list, description="List of error messages")


class IngestStatusResponse(BaseModel):
    """Response model for ingestion status endpoint."""
    total_documents: int = Field(..., description="Total documents in collection")
    total_chunks: int = Field(..., description="Total chunks/vectors in collection")
    last_ingested: Optional[datetime] = Field(None, description="Last ingestion timestamp")
    collection_status: Literal["ready", "empty", "error"] = Field(..., description="Collection status")


# Health Schemas
class ServiceStatus(BaseModel):
    """Status of an individual service."""
    status: Literal["up", "down", "degraded"] = Field(..., description="Service status")
    latency_ms: Optional[int] = Field(None, description="Service response time")
    error: Optional[str] = Field(None, description="Error message if service is down")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall health status")
    services: dict = Field(default_factory=dict, description="Individual service statuses")
    timestamp: Optional[datetime] = Field(None, description="Health check timestamp")


# Error Schemas
class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: Literal[
        "INVALID_QUERY",
        "NO_CONTENT_FOUND",
        "SERVICE_UNAVAILABLE",
        "INTERNAL_ERROR",
        "INGESTION_FAILED",
    ] = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")


# Legacy schemas for backward compatibility
class EmbedRequest(BaseModel):
    """Request model for embedding new content (legacy)."""
    text: str = Field(..., min_length=1, description="Text content to embed")
    source: str = Field(..., description="Source URL or identifier for the content")
    page_title: str = Field(..., description="Title of the source page")
    chunk_id: Optional[str] = Field(None, description="Optional unique ID for the chunk")


class EmbedResponse(BaseModel):
    """Response model for embed endpoint (legacy)."""
    success: bool
    chunk_id: str
    message: str


# ============================================================================
# Subagent Schemas (Constitution v2.0.0)
# ============================================================================

class AgentSummary(BaseModel):
    """Summary of a registered agent."""
    name: str = Field(..., description="Unique agent identifier")
    domain: str = Field(..., description="Domain scope (glossary, hardware, module_info, capstone, book)")
    description: str = Field(..., description="Human-readable description")
    keywords: List[str] = Field(default_factory=list, description="Keywords that trigger this agent")


class AgentListResponse(BaseModel):
    """Response for listing all agents."""
    agents: List[AgentSummary] = Field(..., description="List of registered agents")
    total: int = Field(..., description="Total number of agents")


class AgentDetailResponse(BaseModel):
    """Response for getting a single agent's details."""
    name: str = Field(..., description="Unique agent identifier")
    domain: str = Field(..., description="Domain scope")
    description: str = Field(..., description="Human-readable description")
    keywords: List[str] = Field(default_factory=list, description="Keywords that trigger this agent")
    is_available: bool = Field(True, description="Whether the agent is currently available")


class RouteRequest(BaseModel):
    """Request to preview routing decision."""
    query: str = Field(..., min_length=1, max_length=2000, description="Query to route")


class RouteResponse(BaseModel):
    """Response showing routing decision."""
    primary_agent: str = Field(..., description="Main agent to handle query")
    secondary_agents: List[str] = Field(default_factory=list, description="Additional agents for multi-domain")
    confidence: float = Field(..., ge=0, le=1, description="Routing confidence score")
    reason: str = Field(..., description="Explanation of routing decision")
    is_multi_domain: bool = Field(False, description="Whether query spans multiple domains")


class AgentChatRequest(BaseModel):
    """Request for chatting with a specific agent."""
    query: str = Field(..., min_length=1, max_length=2000, description="The question to ask")
    session_id: Optional[str] = Field(None, description="Optional session ID")
    selected_text: Optional[str] = Field(None, description="Optional selected text context")


class AgentChatResponse(BaseModel):
    """Response from chatting with a specific agent."""
    answer: str = Field(..., description="The agent's response")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    agent_name: str = Field(..., description="Agent that generated the response")
    confidence: float = Field(1.0, ge=0, le=1, description="Response confidence")
    session_id: str = Field(..., description="Session ID")


class MultiAgentResponse(BaseModel):
    """Response from multi-agent coordination."""
    answer: str = Field(..., description="Synthesized response from multiple agents")
    citations: List[Citation] = Field(default_factory=list, description="Combined citations")
    agents_used: List[str] = Field(..., description="List of agents that contributed")
    session_id: str = Field(..., description="Session ID")
