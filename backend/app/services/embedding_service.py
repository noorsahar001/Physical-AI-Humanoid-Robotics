"""
Embedding service for generating text embeddings.
Constitution v1.2.0: Supports OpenAI embeddings and Google Gemini native embeddings.
With exponential backoff retry for Gemini free tier rate limits.
"""

from typing import List, Optional, Any
import logging
import time
import random

from app.config import settings

logger = logging.getLogger(__name__)

# Retry configuration for Gemini free tier
MAX_RETRIES = 5
BASE_DELAY = 1.0  # Starting delay in seconds
MAX_DELAY = 60.0  # Maximum delay between retries
JITTER = 0.5  # Random jitter factor


def exponential_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(-JITTER, JITTER) * delay
    return delay + jitter


class EmbeddingService:
    """Service class for generating text embeddings with retry logic."""

    def __init__(self):
        self.embeddings: Optional[Any] = None
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._use_google_native = False

    def connect(self) -> None:
        """Initialize the embeddings client based on provider."""
        if self.embeddings is None:
            if settings.LLM_PROVIDER.lower() == "google" or (settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY):
                self._init_google_embeddings()
            else:
                self._init_openai_embeddings()

    def _init_google_embeddings(self) -> None:
        """Initialize Google Generative AI embeddings."""
        try:
            import google.generativeai as genai
        except ImportError:
            logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
            raise

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Google embeddings")

        genai.configure(api_key=api_key)
        self._use_google_native = True
        self.embeddings = genai
        logger.info(f"Embedding service initialized with Google GenAI model: {self.model}")

    def _init_openai_embeddings(self) -> None:
        """Initialize OpenAI embeddings."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            logger.error("langchain_openai package not installed. Run: pip install langchain_openai")
            raise

        api_key = settings.OPENAI_API_KEY or getattr(settings, "active_api_key", None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            openai_api_key=api_key,
        )
        self._use_google_native = False
        logger.info(f"Embedding service initialized with OpenAI model: {self.model}")

    def _call_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry.

        Handles:
        - 429: Resource exhausted (rate limit)
        - 503: Service unavailable
        - Connection errors
        """
        last_exception = None

        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check if error is retryable
                is_rate_limit = "429" in str(e) or "resource exhausted" in error_str or "quota" in error_str
                is_service_error = "503" in str(e) or "service unavailable" in error_str or "temporarily" in error_str
                is_connection_error = "connection" in error_str or "timeout" in error_str or "socket" in error_str

                if is_rate_limit or is_service_error or is_connection_error:
                    if attempt < MAX_RETRIES - 1:
                        delay = exponential_backoff(attempt)
                        logger.warning(
                            f"Embedding API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Max retries reached for embedding API: {e}")
                else:
                    # Non-retryable error, raise immediately
                    logger.error(f"Non-retryable embedding error: {e}")
                    raise

        # If we exhausted all retries, raise the last exception
        raise last_exception

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts with retry logic."""
        if not texts:
            return []

        def _generate():
            embeddings = []
            if self._use_google_native:
                for text in texts:
                    result = self.embeddings.embed_content(
                        model=f"models/{self.model}",
                        content=text,
                        task_type="retrieval_document",
                    )
                    embeddings.append(result['embedding'])
                logger.info(f"Generated {len(embeddings)} embeddings via Google GenAI")
            else:
                embeddings = self.embeddings.embed_documents(texts)
                logger.info(f"Generated {len(embeddings)} embeddings via OpenAI")
            return embeddings

        try:
            return self._call_with_retry(_generate)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text with retry logic."""
        def _generate():
            if self._use_google_native:
                result = self.embeddings.embed_content(
                    model=f"models/{self.model}",
                    content=text,
                    task_type="retrieval_query",
                )
                return result['embedding']
            else:
                return self.embeddings.embed_query(text)

        try:
            return self._call_with_retry(_generate)
        except Exception as e:
            logger.error(f"Error generating embedding for text [{text[:30]}...]: {e}")
            raise

    def generate_embedding_safe(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding with graceful fallback.

        Returns None instead of raising exception on failure.
        Useful for non-critical paths.
        """
        try:
            return self.generate_embedding(text)
        except Exception as e:
            logger.warning(f"Safe embedding generation failed, returning None: {e}")
            return None

    def health_check(self) -> bool:
        """Check if the embedding service is healthy."""
        if self.embeddings is None:
            logger.warning("Embedding service not initialized")
            return False
        try:
            test_embedding = self.generate_embedding("test")
            actual_dim = len(test_embedding)
            if actual_dim != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {actual_dim}")
                self.dimension = actual_dim
            return True
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        _embedding_service.connect()
    return _embedding_service
