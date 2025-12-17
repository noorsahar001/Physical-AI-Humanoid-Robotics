"""
Ingestion API routes for the RAG Chatbot.
Constitution v1.1.0: Provides content ingestion endpoints.
"""

from fastapi import APIRouter, HTTPException
import logging

from app.models.schemas import IngestRequest, IngestResponse, IngestStatusResponse
from app.services.ingestion_service import get_ingestion_service
from app.services.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_content(request: IngestRequest):
    """
    Ingest book content into the vector database.

    This endpoint processes MDX/MD files from the docs directory,
    chunks them, generates embeddings, and stores them in Qdrant.
    """
    try:
        ingestion_service = get_ingestion_service()

        result = ingestion_service.ingest_documents(
            docs_path=request.docs_path,
            force_reingest=request.force_reingest,
        )

        return IngestResponse(**result)

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/ingest/status", response_model=IngestStatusResponse)
async def get_ingest_status():
    """
    Get the current status of ingested content.

    Returns information about the number of documents and chunks
    in the vector database.
    """
    try:
        qdrant_service = get_qdrant_service()
        collection_info = qdrant_service.get_collection_info()

        points_count = collection_info.get("points_count", 0)
        status = collection_info.get("status", "unknown")

        # Determine collection status
        if status == "green" or points_count > 0:
            collection_status = "ready"
        elif points_count == 0:
            collection_status = "empty"
        else:
            collection_status = "error"

        return IngestStatusResponse(
            total_documents=0,  # We don't track this separately
            total_chunks=points_count or 0,
            last_ingested=None,  # Would need to track this
            collection_status=collection_status,
        )

    except Exception as e:
        logger.error(f"Error getting ingest status: {e}")
        return IngestStatusResponse(
            total_documents=0,
            total_chunks=0,
            last_ingested=None,
            collection_status="error",
        )
