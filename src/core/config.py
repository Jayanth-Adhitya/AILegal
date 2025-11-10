"""Configuration settings for AI Legal Assistant."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API Configuration
    google_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"

    # Groq API Configuration
    groq_api_key: Optional[str] = None

    # ChromaDB Configuration
    chroma_db_path: str = "./data/chroma_db"
    chroma_collection_name: str = "legal_policies"

    # Application Settings
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"
    policies_dir: str = "./data/policies"
    max_file_size_mb: int = 50

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Generation Configuration
    temperature: float = 0.1  # Low temperature for consistent legal analysis
    max_output_tokens: int = 32768  # Increased for batch analysis (Gemini 2.0 supports up to 65k)
    top_p: float = 0.95
    top_k: int = 40

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 3  # Number of relevant policies to retrieve

    # Batch Processing Configuration
    batch_mode: bool = True  # Enable batch processing by default
    max_batch_size: int = 50  # Maximum clauses per batch
    batch_chunk_threshold: int = 900000  # Token threshold for chunking
    rate_limit_retry_attempts: int = 3  # Retry attempts for rate limits
    requests_per_minute: int = 15  # RPM limit for free tier
    requests_per_day: int = 250  # Daily quota for free tier

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
