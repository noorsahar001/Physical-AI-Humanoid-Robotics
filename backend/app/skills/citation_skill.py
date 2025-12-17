"""
Citation Skill for formatting source references.
Constitution v2.0.0: Shared skill for all subagents (Principle V - Citations).
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CitationSkill:
    """
    Skill for formatting citations and source references.

    Provides consistent [Source N] formatting across all agents.
    Can be injected into any agent that returns cited responses.
    """

    def format_citations(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Format retrieved chunks into citation objects.

        Args:
            chunks: List of retrieved content chunks

        Returns:
            List of citation dictionaries with index, source, title, section, relevance_score
        """
        citations = []
        for i, chunk in enumerate(chunks, 1):
            citations.append({
                "index": i,
                "source": chunk.get("source", ""),
                "title": chunk.get("title", ""),
                "section": chunk.get("section"),
                "relevance_score": chunk.get("score", 0),
            })

        logger.debug(f"CitationSkill formatted {len(citations)} citations")
        return citations

    def build_context_with_citations(
        self,
        chunks: List[Dict[str, Any]],
        selected_text: str = None,
    ) -> str:
        """
        Build a context string with numbered source references.

        Args:
            chunks: List of retrieved content chunks
            selected_text: Optional user-selected text to prioritize

        Returns:
            Formatted context string with [Source N] labels
        """
        context_parts = []

        if selected_text:
            context_parts.append(f"USER SELECTED TEXT:\n{selected_text}\n")

        if chunks:
            context_parts.append("RELEVANT BOOK CONTENT:")
            for i, chunk in enumerate(chunks, 1):
                source = chunk.get("source", "Unknown")
                title = chunk.get("title", "Unknown")
                section = chunk.get("section", "")
                text = chunk.get("text", "")
                section_info = f" > {section}" if section else ""
                context_parts.append(
                    f"\n[Source {i}] {title}{section_info}\nPath: {source}\n{text}"
                )
        else:
            context_parts.append(
                "No relevant content found in the book for this query."
            )

        return "\n".join(context_parts)

    def extract_source_text(
        self,
        citation: Dict[str, Any],
        chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Extract the original text for a given citation.

        Args:
            citation: Citation dictionary with index
            chunks: Original list of content chunks

        Returns:
            The text content for the citation, or empty string if not found
        """
        index = citation.get("index", 0)
        if 0 < index <= len(chunks):
            return chunks[index - 1].get("text", "")
        return ""

    def format_inline_reference(
        self,
        index: int,
        title: str = None,
    ) -> str:
        """
        Format an inline citation reference.

        Args:
            index: The citation index (1-based)
            title: Optional title to include

        Returns:
            Formatted inline reference string like "[Source 1]"
        """
        if title:
            return f"[Source {index}: {title}]"
        return f"[Source {index}]"
