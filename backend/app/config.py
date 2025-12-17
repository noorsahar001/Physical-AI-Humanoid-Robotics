"""
Configuration management for the RAG Chatbot Backend.
Loads environment variables using pydantic-settings.
Constitution v1.1.0: Python 3.13, FastAPI, Uvicorn, LangChain, Qdrant
Updated for Gemini 2.5 Flash support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys - supports both OpenAI and Gemini
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key for embeddings and LLM")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Gemini API key for embeddings and LLM")

    # LLM Configuration
    # Default to google provider when GEMINI_API_KEY is set
    LLM_PROVIDER: str = Field(default="google", description="LLM provider: openai, google")
    LLM_MODEL: str = Field(default="gemini-2.5-flash", description="LLM model name")
    LLM_BASE_URL: Optional[str] = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        description="Custom LLM base URL (for Gemini OpenAI compat)"
    )

    # Embedding Configuration
    # Default to Gemini text-embedding-004 for Google provider
    EMBEDDING_MODEL: str = Field(default="text-embedding-004", description="Embedding model name")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Embedding vector dimension")

    # Qdrant Configuration
    QDRANT_HOST: str = Field(default="localhost", description="Qdrant host")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant port")
    QDRANT_URL: Optional[str] = Field(default=None, description="Full Qdrant URL (overrides host/port)")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant API key (for cloud)")
    QDRANT_COLLECTION: str = Field(default="physical_ai_book", description="Qdrant collection name")
    QDRANT_COLLECTION_NAME: Optional[str] = Field(default=None, description="Alias for QDRANT_COLLECTION")

    # Book Content Path
    DOCS_PATH: str = Field(default="../physical-ai-humanoid-robotics/docs", description="Path to book docs")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000", description="Comma-separated CORS origins")

    # Debug
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Neon Database (optional)
    NEON_DATABASE_URL: Optional[str] = Field(default=None, description="Neon Serverless Postgres URL")

    @model_validator(mode='after')
    def resolve_aliases_and_validate(self):
        """Resolve aliases and validate required fields."""
        # Resolve QDRANT_COLLECTION_NAME alias
        if self.QDRANT_COLLECTION_NAME and not self.QDRANT_COLLECTION:
            self.QDRANT_COLLECTION = self.QDRANT_COLLECTION_NAME
        elif self.QDRANT_COLLECTION_NAME:
            # Prefer QDRANT_COLLECTION_NAME if both are set
            self.QDRANT_COLLECTION = self.QDRANT_COLLECTION_NAME

        # Auto-detect provider from available API keys
        if self.GEMINI_API_KEY and not self.OPENAI_API_KEY:
            if self.LLM_PROVIDER == "openai":
                self.LLM_PROVIDER = "google"

        # Set defaults based on provider
        if self.LLM_PROVIDER == "google":
            # Use Gemini defaults if not explicitly set
            if self.LLM_MODEL == "gpt-4o-mini":
                self.LLM_MODEL = "gemini-2.5-flash"
            if self.EMBEDDING_MODEL == "text-embedding-3-small":
                self.EMBEDDING_MODEL = "text-embedding-004"
            if self.EMBEDDING_DIMENSION == 1536:
                self.EMBEDDING_DIMENSION = 768
            if not self.LLM_BASE_URL:
                self.LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"

        return self

    @property
    def active_api_key(self) -> str:
        """Get the active API key based on provider."""
        if self.LLM_PROVIDER == "google" and self.GEMINI_API_KEY:
            return self.GEMINI_API_KEY
        return self.OPENAI_API_KEY or self.GEMINI_API_KEY or ""

    @property
    def qdrant_url(self) -> str:
        """Build Qdrant URL from host and port, or use explicit URL."""
        if self.QDRANT_URL:
            return self.QDRANT_URL
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    @property
    def is_qdrant_cloud(self) -> bool:
        """Check if using Qdrant Cloud."""
        return bool(self.QDRANT_API_KEY) or (self.QDRANT_URL and "cloud.qdrant.io" in self.QDRANT_URL)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
