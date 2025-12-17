"""
FastAPI application entry point for the RAG Chatbot Backend.
Constitution v2.0.0: Python 3.13, FastAPI, Uvicorn, LangChain, Qdrant
With subagent routing support.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.qdrant_service import get_qdrant_service
from app.services.embedding_service import get_embedding_service
from app.agents import register_all_agents

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting RAG Chatbot Backend (Constitution v2.0.0)...")
    try:
        # Initialize Qdrant connection
        qdrant_service = get_qdrant_service()
        logger.info("Qdrant service initialized")

        # Initialize embedding service
        embedding_service = get_embedding_service()
        logger.info("Embedding service initialized")

        # Register all subagents (Constitution v2.0.0)
        agent_count = register_all_agents(
            qdrant_service=qdrant_service,
            embedding_service=embedding_service,
        )
        logger.info(f"Registered {agent_count} agents")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot Backend...")


# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description="A RAG-powered chatbot for the Physical AI & Humanoid Robotics book with subagent routing. Constitution v2.0.0.",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "RAG Chatbot API is running",
        "version": "2.0.0",
        "constitution": "v1.1.0",
        "docs": "/docs",
        "health": "/health",
        "chat": "/api/chatbot/chat",
        "ingest": "/api/chatbot/ingest",
    }


# Register routers
from app.routes.chat import router as chat_router
from app.routes.ingest import router as ingest_router
from app.routes.health import router as health_router
from app.routes.agents import router as agents_router

app.include_router(chat_router, prefix="/api/chatbot", tags=["Chat"])
app.include_router(ingest_router, prefix="/api/chatbot", tags=["Ingestion"])
app.include_router(health_router, tags=["Health"])
app.include_router(agents_router, prefix="/api", tags=["Agents"])


# Error handlers
from fastapi import Request
from fastapi.responses import JSONResponse
from app.models.schemas import ErrorResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error": str(exc)} if settings.DEBUG else None,
        ).model_dump(),
    )
