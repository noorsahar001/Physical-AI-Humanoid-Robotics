"""
Health check API routes for the RAG Chatbot.
Constitution v1.1.0: Service health monitoring.
"""

from fastapi import APIRouter
from datetime import datetime
import time
import logging

from app.models.schemas import HealthResponse, ServiceStatus
from app.services.qdrant_service import get_qdrant_service
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()


def check_qdrant_health() -> ServiceStatus:
    """Check Qdrant service health."""
    start_time = time.time()
    try:
        qdrant_service = get_qdrant_service()
        is_healthy = qdrant_service.health_check()
        latency_ms = int((time.time() - start_time) * 1000)

        if is_healthy:
            return ServiceStatus(status="up", latency_ms=latency_ms)
        else:
            return ServiceStatus(status="down", latency_ms=latency_ms, error="Health check failed")
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ServiceStatus(status="down", latency_ms=latency_ms, error=str(e))


def check_embedding_health() -> ServiceStatus:
    """Check embedding service (LLM) health."""
    start_time = time.time()
    try:
        embedding_service = get_embedding_service()
        is_healthy = embedding_service.health_check()
        latency_ms = int((time.time() - start_time) * 1000)

        if is_healthy:
            return ServiceStatus(status="up", latency_ms=latency_ms)
        else:
            return ServiceStatus(status="degraded", latency_ms=latency_ms, error="Embedding dimension mismatch")
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ServiceStatus(status="down", latency_ms=latency_ms, error=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of all system components.

    Returns the status of:
    - API service (always up if this endpoint responds)
    - Qdrant vector database
    - LLM/Embedding service (OpenAI API)
    """
    # API is always up if we can respond
    api_status = ServiceStatus(status="up", latency_ms=0)

    # Check other services
    qdrant_status = check_qdrant_health()
    llm_status = check_embedding_health()

    # Determine overall status
    services = {
        "api": api_status.model_dump(),
        "qdrant": qdrant_status.model_dump(),
        "llm": llm_status.model_dump(),
    }

    all_statuses = [api_status.status, qdrant_status.status, llm_status.status]

    if all(s == "up" for s in all_statuses):
        overall_status = "healthy"
    elif any(s == "down" for s in all_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.utcnow(),
    )
