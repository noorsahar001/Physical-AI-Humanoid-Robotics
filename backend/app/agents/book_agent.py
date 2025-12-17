"""
Book Agent for RAG-based question answering about the Physical AI & Humanoid Robotics book.
Constitution v1.1.0: Uses LangChain for LLM orchestration.
With Gemini 2.5 Flash support and exponential backoff retry.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import asyncio
import random

from app.config import settings
from app.services.qdrant_service import QdrantService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Retry configuration for Gemini free tier
MAX_LLM_RETRIES = 5
BASE_DELAY = 2.0
MAX_DELAY = 60.0
JITTER = 0.5

# System prompt for the book agent (Constitution Principle V: Citations required)
BOOK_AGENT_SYSTEM_PROMPT = """You are an AI assistant specialized in the "Physical AI & Humanoid Robotics" book.

Your responsibilities:
1. Answer questions truthfully and ONLY using the provided book content.
2. If you cannot find relevant information in the provided context, respond with:
   "I couldn't find relevant information in the book for your question."
3. ALWAYS cite your sources using [Source N] format where N is the source number.
4. If the user provides selected text, prioritize that context first.

Topics covered in the book:
- Physical AI & Humanoid Robotics
- ROS 2, Gazebo, Unity, NVIDIA Isaac
- VLA (Vision-Language-Action)
- Sensors: LIDAR, IMU, Cameras
- Capstone Humanoid Project

Response format:
- Be concise and informative
- Use markdown formatting when appropriate
- Include citations as [Source N] inline where you reference information
- At the end, list all sources used with their titles
"""

# Fallback response when all retries fail
FALLBACK_RESPONSE = """I apologize, but I'm currently experiencing technical difficulties and cannot process your request at this time.

This could be due to:
- High demand on the AI service
- Temporary service unavailability

Please try again in a few moments. If the issue persists, the service may be under maintenance."""


def exponential_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(-JITTER, JITTER) * delay
    return delay + jitter


class BookAgent:
    """Agent for answering questions about the book using LangChain RAG."""

    def __init__(
        self,
        qdrant_service: QdrantService,
        embedding_service: EmbeddingService,
    ):
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self.llm = self._create_llm()

    def _create_llm(self) -> ChatOpenAI:
        """Create LLM instance with proper configuration for Gemini."""
        api_key = settings.active_api_key

        # Build LLM kwargs
        llm_kwargs = {
            "model": settings.LLM_MODEL,
            "api_key": api_key,  # Use api_key (newer) instead of openai_api_key (deprecated)
            "temperature": 0.3,
            "max_tokens": 2048,
            "streaming": True,
            "timeout": 60,  # 60 second timeout
            "max_retries": 0,  # We handle retries ourselves
        }

        # Add base URL for Gemini OpenAI-compatible endpoint
        if settings.LLM_BASE_URL:
            # Ensure no double slashes and proper format
            base_url = settings.LLM_BASE_URL.rstrip('/')
            llm_kwargs["base_url"] = base_url  # Use base_url (newer) instead of openai_api_base

        logger.info(f"LLM configured: model={settings.LLM_MODEL}, base_url={settings.LLM_BASE_URL}")
        return ChatOpenAI(**llm_kwargs)

    def retrieve_book_content(
        self, query: str, limit: int = 5, score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search the book content in Qdrant for relevant information.

        Args:
            query: The search query
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of relevant content chunks with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)

            # Search Qdrant
            results = self.qdrant_service.search_vectors(
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
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
                })

            logger.info(f"Retrieved {len(formatted_results)} chunks for query: {query[:50]}...")
            return formatted_results
        except Exception as e:
            logger.error(f"Error retrieving book content: {e}")
            return []

    def _build_context(
        self,
        retrieved_content: List[Dict[str, Any]],
        selected_text: Optional[str] = None,
    ) -> str:
        """Build the context string from retrieved content with numbered sources."""
        context_parts = []

        if selected_text:
            context_parts.append(f"USER SELECTED TEXT:\n{selected_text}\n")

        if retrieved_content:
            context_parts.append("RELEVANT BOOK CONTENT:")
            for i, chunk in enumerate(retrieved_content, 1):
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

    def _extract_citations(
        self, retrieved_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract citation information from retrieved content."""
        citations = []
        for i, chunk in enumerate(retrieved_content, 1):
            citations.append({
                "index": i,
                "source": chunk.get("source", ""),
                "title": chunk.get("title", ""),
                "section": chunk.get("section"),
                "relevance_score": chunk.get("score", 0),
            })
        return citations

    async def _stream_with_retry(
        self,
        messages: List,
        max_retries: int = MAX_LLM_RETRIES,
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response with exponential backoff retry.

        Handles 429 (rate limit) and 503 (service unavailable) errors.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        yield chunk.content
                return  # Success, exit the retry loop
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check if error is retryable
                is_rate_limit = "429" in str(e) or "resource exhausted" in error_str or "quota" in error_str
                is_service_error = "503" in str(e) or "service unavailable" in error_str or "temporarily" in error_str
                is_connection_error = "connection" in error_str or "timeout" in error_str or "socket" in error_str

                if is_rate_limit or is_service_error or is_connection_error:
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt)
                        logger.warning(
                            f"LLM API error (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Max retries reached for LLM API: {e}")
                else:
                    # Non-retryable error
                    logger.error(f"Non-retryable LLM error: {e}")
                    raise

        # If we exhausted all retries, yield fallback response
        logger.error(f"LLM call failed after {max_retries} attempts: {last_exception}")
        yield FALLBACK_RESPONSE

    async def run_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        selected_text: Optional[str] = None,
    ) -> AsyncGenerator[tuple, None]:
        """
        Run the agent and stream the response using LangChain.

        Args:
            query: The user's question
            chat_history: Previous messages in the conversation
            selected_text: Optional text selected by the user

        Yields:
            Tuples of (type, content) where type is "text", "source", or "end"
        """
        chat_history = chat_history or []

        # Retrieve relevant content
        retrieved_content = self.retrieve_book_content(query)

        # Check if we found relevant content (Constitution Principle I)
        has_relevant_content = len(retrieved_content) > 0

        # Build context
        context = self._build_context(retrieved_content, selected_text)

        # Build messages for LangChain
        messages = [SystemMessage(content=BOOK_AGENT_SYSTEM_PROMPT)]

        # Add chat history (limited to last 10 messages)
        for msg in chat_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Add the current query with context
        user_message = f"""Context from the book:
{context}

User Question: {query}

Please answer based on the provided context. If the information is not in the context, say "I couldn't find relevant information in the book for your question." Always cite sources using [Source N] format."""

        messages.append(HumanMessage(content=user_message))

        try:
            # Stream the response using LangChain with retry
            async for chunk in self._stream_with_retry(messages):
                yield ("text", chunk)

            # Yield citations after the main response (Constitution Principle V)
            if has_relevant_content:
                citations = self._extract_citations(retrieved_content)
                for citation in citations:
                    yield ("source", citation)

            yield ("end", "")

        except Exception as e:
            logger.error(f"Error in agent stream: {e}")
            yield ("text", f"Sorry, an error occurred while processing your request: {str(e)}")
            yield ("end", "")

    async def run(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        selected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the agent and return the complete response.

        Args:
            query: The user's question
            chat_history: Previous messages in the conversation
            selected_text: Optional text selected by the user

        Returns:
            Dictionary with response and sources
        """
        full_response = ""
        sources = []

        async for chunk_type, content in self.run_stream(query, chat_history, selected_text):
            if chunk_type == "text":
                full_response += content
            elif chunk_type == "source":
                sources.append(content)

        return {
            "response": full_response,
            "sources": sources,
        }
