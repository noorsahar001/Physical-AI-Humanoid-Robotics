"""
RAG Skill for domain-filtered retrieval from vector database.
Constitution v2.0.0: Shared skill for all subagents.
"""

from typing import List, Dict, Any, Optional
import logging

from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class RAGSkill:
    """
    Skill for RAG (Retrieval-Augmented Generation) operations.

    Provides domain-filtered retrieval from the Qdrant vector database.
    Can be injected into any agent that needs to retrieve book content.
    """

    def __init__(self, qdrant_service, embedding_service):
        """
        Initialize the RAG skill with required services.

        Args:
            qdrant_service: QdrantService instance for vector operations
            embedding_service: EmbeddingService instance for generating embeddings
        """
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def retrieve(
        self,
        query: str,
        domain_filter: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content chunks from the vector database.

        Args:
            query: The search query
            domain_filter: Optional domain to filter results (e.g., "glossary", "hardware")
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of retrieved chunks with text, source, title, section, score, domain
        """
        # Generate cache key
        cache_key = f"{query}:{domain_filter}:{limit}"
        if cache_key in self._cache:
            logger.debug(f"RAGSkill cache hit for query: {query[:50]}...")
            return self._cache[cache_key]

        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)

            # Build filter condition if domain is specified
            filter_condition = None
            if domain_filter:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="domain",
                            match=MatchValue(value=domain_filter)
                        )
                    ]
                )

            # Search Qdrant - now filter_condition is properly supported
            results = self.qdrant_service.search_vectors(
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filter_condition=filter_condition,
            )

            # Format results
            formatted_results = []
            for result in results:
                payload = result.get("payload", {})
                formatted_results.append({
                    "text": payload.get("text", ""),
                    "source": payload.get("source", ""),
                    "title": payload.get("title", payload.get("page_title", "")),
                    "section": payload.get("section", ""),
                    "score": result.get("score", 0),
                    "domain": payload.get("domain", "general"),
                })

            # Cache results
            self._cache[cache_key] = formatted_results

            logger.info(
                f"RAGSkill retrieved {len(formatted_results)} chunks "
                f"(domain={domain_filter}, query={query[:50]}...)"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"RAGSkill retrieval error: {e}")
            # Return empty list on error to allow graceful degradation
            return []

    def retrieve_multi_domain(
        self,
        query: str,
        domains: List[str],
        limit_per_domain: int = 3,
        score_threshold: float = 0.3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve content from multiple domains.

        Args:
            query: The search query
            domains: List of domains to search
            limit_per_domain: Maximum results per domain
            score_threshold: Minimum similarity score threshold

        Returns:
            Dictionary mapping domain names to their retrieved chunks
        """
        results = {}
        for domain in domains:
            results[domain] = self.retrieve(
                query=query,
                domain_filter=domain,
                limit=limit_per_domain,
                score_threshold=score_threshold,
            )
        return results

    def clear_cache(self):
        """Clear the retrieval cache."""
        self._cache.clear()
        logger.info("RAGSkill cache cleared")
