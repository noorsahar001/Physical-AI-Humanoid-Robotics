"""
Qdrant vector store service for storing and searching book content embeddings.
Constitution v1.1.0: Qdrant as vector storage.
Compatible with qdrant-client v1.7+ through v1.16+.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter
from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4
import time

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service class for Qdrant vector database operations."""

    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.QDRANT_COLLECTION

    def connect(self) -> None:
        """Initialize the Qdrant client."""
        if self.client is None:
            try:
                if settings.is_qdrant_cloud:
                    self.client = QdrantClient(
                        url=settings.qdrant_url,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=30,  # 30 second timeout
                    )
                    logger.info(f"Qdrant client connecting to cloud: {settings.qdrant_url[:50]}...")
                else:
                    self.client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        timeout=30,
                    )
                    logger.info(f"Qdrant client connecting to local: {settings.qdrant_url}")

                self._ensure_collection_exists()
                logger.info(f"Qdrant client connected, collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise

    def _ensure_collection_exists(self) -> None:
        """Create the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        default_segment_number=1,
                    ),
                    on_disk_payload=True,
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def upsert_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> bool:
        """Insert or update vectors in the collection."""
        if ids is None:
            ids = [str(uuid4()) for _ in vectors]

        points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Upserted {len(points)} vectors to collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise

    def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.3,
        filter_condition: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the collection.

        Compatible with qdrant-client v1.7+ through v1.16+.
        Uses query_points (v1.7+) with fallback to search (older versions).

        Args:
            query_vector: The embedding vector to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filter_condition: Optional Qdrant Filter for domain filtering

        Returns:
            List of results with id, score, and payload
        """
        formatted_results = []

        try:
            # Try query_points first (v1.7+, preferred in v1.16+)
            # In v1.16+, query_points accepts 'query' as vector directly
            try:
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=filter_condition,
                    with_payload=True,
                    with_vectors=False,
                )

                # v1.16+ returns QueryResponse with .points attribute
                for point in response.points:
                    formatted_results.append({
                        "id": point.id,
                        "score": point.score,
                        "payload": point.payload or {},
                    })

            except AttributeError:
                # Fallback: response might be structured differently in older versions
                # Try accessing points directly
                if hasattr(response, 'points'):
                    points = response.points
                elif isinstance(response, list):
                    points = response
                else:
                    points = []

                for point in points:
                    formatted_results.append({
                        "id": getattr(point, 'id', None),
                        "score": getattr(point, 'score', 0),
                        "payload": getattr(point, 'payload', {}) or {},
                    })

        except (TypeError, AttributeError) as e:
            # Fallback to legacy search method for older clients
            logger.warning(f"query_points failed ({e}), falling back to search method")
            try:
                response = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=filter_condition,
                    with_payload=True,
                    with_vectors=False,
                )

                for point in response:
                    formatted_results.append({
                        "id": point.id,
                        "score": point.score,
                        "payload": point.payload or {},
                    })
            except Exception as search_error:
                logger.error(f"Both query_points and search failed: {search_error}")
                raise

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

        logger.info(f"Found {len(formatted_results)} results for vector search")
        return formatted_results

    def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=ids),
            )
            logger.info(f"Deleted {len(ids)} vectors from collection")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection safely."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": getattr(info, "vectors_count", 0),
                "points_count": getattr(info, "points_count", 0),
                "status": getattr(info.status, "value", "unknown") if info.status else "unknown",
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "name": self.collection_name,
                "vectors_count": 0,
                "points_count": 0,
                "status": "error",
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant service instance
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get or create the Qdrant service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
        _qdrant_service.connect()
    return _qdrant_service
