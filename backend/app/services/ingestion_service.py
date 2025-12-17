"""
Ingestion service for processing book content and storing in Qdrant.
Constitution v1.1.0: RAG pipeline with embeddings and Qdrant.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting book content into the vector database."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
    ):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service

        # Configure text splitter per spec (400 tokens, 50 overlap)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1600,  # ~400 tokens (4 chars per token avg)
            chunk_overlap=200,  # ~50 tokens overlap
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Track processed documents by hash
        self._document_hashes: Dict[str, str] = {}

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, str], str]:
        """Extract YAML frontmatter from MDX/MD content."""
        frontmatter = {}
        body = content

        # Check for frontmatter delimiter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_content = parts[1].strip()
                body = parts[2].strip()

                # Parse simple YAML-like frontmatter
                for line in fm_content.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip().strip('"').strip("'")

        return frontmatter, body

    def _extract_title(self, frontmatter: Dict[str, str], content: str, file_path: str) -> str:
        """Extract document title from frontmatter or first heading."""
        # Try frontmatter title
        if "title" in frontmatter:
            return frontmatter["title"]

        # Try sidebar_label
        if "sidebar_label" in frontmatter:
            return frontmatter["sidebar_label"]

        # Try first H1 heading
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Fallback to filename
        return Path(file_path).stem.replace("-", " ").replace("_", " ").title()

    def _extract_section_hierarchy(self, content: str, chunk_start: int) -> str:
        """Extract section heading hierarchy for a chunk position."""
        # Find all headings before the chunk position
        headings = []
        current_level = 0

        for match in re.finditer(r"^(#{1,6})\s+(.+)$", content[:chunk_start], re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()

            # Maintain hierarchy
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, title))

        if headings:
            return " > ".join(h[1] for h in headings)
        return ""

    def _load_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse an MDX/MD document."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, body = self._extract_frontmatter(content)
            title = self._extract_title(frontmatter, body, file_path)

            # Get relative path for source reference
            docs_path = Path(settings.DOCS_PATH).resolve()
            file_path_resolved = Path(file_path).resolve()

            try:
                rel_path = file_path_resolved.relative_to(docs_path)
            except ValueError:
                rel_path = file_path_resolved.name

            return {
                "file_path": str(file_path),
                "relative_path": str(rel_path),
                "title": title,
                "frontmatter": frontmatter,
                "content": body,
                "content_hash": self._compute_hash(body),
            }
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return None

    def _chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split document into chunks with metadata."""
        content = document["content"]
        chunks = []

        # Split content into chunks
        text_chunks = self.text_splitter.split_text(content)

        # Track position in original content for section extraction
        current_pos = 0

        for i, chunk_text in enumerate(text_chunks):
            # Find position of this chunk in original content
            chunk_pos = content.find(chunk_text, current_pos)
            if chunk_pos == -1:
                chunk_pos = current_pos

            section = self._extract_section_hierarchy(content, chunk_pos)
            current_pos = chunk_pos + len(chunk_text)

            chunks.append({
                "text": chunk_text,
                "source": document["relative_path"],
                "title": document["title"],
                "section": section,
                "position": i,
                "document_hash": document["content_hash"],
            })

        logger.info(f"Created {len(chunks)} chunks from {document['title']}")
        return chunks

    def _should_process_document(self, doc_hash: str, file_path: str) -> bool:
        """Check if document should be processed (new or changed)."""
        cached_hash = self._document_hashes.get(file_path)
        return cached_hash != doc_hash

    def discover_documents(self, docs_path: Optional[str] = None) -> List[str]:
        """Discover all MDX/MD files in the docs directory."""
        docs_path = docs_path or settings.DOCS_PATH
        docs_dir = Path(docs_path)

        if not docs_dir.exists():
            logger.error(f"Docs directory not found: {docs_dir}")
            return []

        # Find all .md and .mdx files
        files = []
        for pattern in ["**/*.md", "**/*.mdx"]:
            files.extend(docs_dir.glob(pattern))

        # Filter out any hidden files or directories
        files = [f for f in files if not any(part.startswith(".") for part in f.parts)]

        logger.info(f"Discovered {len(files)} documents in {docs_path}")
        return [str(f) for f in files]

    def ingest_documents(
        self,
        docs_path: Optional[str] = None,
        force_reingest: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest all documents from the docs directory.

        Args:
            docs_path: Path to documents directory
            force_reingest: Force re-ingestion of all documents

        Returns:
            Dictionary with ingestion results
        """
        docs_path = docs_path or settings.DOCS_PATH

        result = {
            "status": "success",
            "documents_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        # Discover documents
        file_paths = self.discover_documents(docs_path)

        if not file_paths:
            result["status"] = "failed"
            result["errors"].append(f"No documents found in {docs_path}")
            return result

        all_chunks = []

        for file_path in file_paths:
            try:
                # Load document
                document = self._load_document(file_path)
                if not document:
                    result["errors"].append(f"Failed to load: {file_path}")
                    continue

                # Check if we need to process this document
                if not force_reingest and not self._should_process_document(
                    document["content_hash"], file_path
                ):
                    logger.info(f"Skipping unchanged document: {file_path}")
                    continue

                # Chunk document
                chunks = self._chunk_document(document)
                all_chunks.extend(chunks)

                # Update hash cache
                self._document_hashes[file_path] = document["content_hash"]
                result["documents_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                result["errors"].append(f"Error processing {file_path}: {str(e)}")

        # Generate embeddings and store in Qdrant
        if all_chunks:
            try:
                texts = [chunk["text"] for chunk in all_chunks]
                embeddings = self.embedding_service.generate_embeddings(texts)

                # Prepare payloads
                payloads = []
                for chunk in all_chunks:
                    payloads.append({
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "title": chunk["title"],
                        "section": chunk["section"],
                        "position": chunk["position"],
                    })

                # Upsert to Qdrant
                self.qdrant_service.upsert_vectors(embeddings, payloads)
                result["chunks_created"] = len(all_chunks)

            except Exception as e:
                logger.error(f"Error storing embeddings: {e}")
                result["status"] = "partial"
                result["errors"].append(f"Error storing embeddings: {str(e)}")

        if result["errors"] and result["documents_processed"] == 0:
            result["status"] = "failed"
        elif result["errors"]:
            result["status"] = "partial"

        logger.info(
            f"Ingestion complete: {result['documents_processed']} docs, "
            f"{result['chunks_created']} chunks"
        )
        return result


# Global ingestion service instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service(
    embedding_service: Optional[EmbeddingService] = None,
    qdrant_service: Optional[QdrantService] = None,
) -> IngestionService:
    """Get or create the ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        from app.services.embedding_service import get_embedding_service
        from app.services.qdrant_service import get_qdrant_service

        embedding_svc = embedding_service or get_embedding_service()
        qdrant_svc = qdrant_service or get_qdrant_service()
        _ingestion_service = IngestionService(embedding_svc, qdrant_svc)
    return _ingestion_service
