"""Configuration settings for AI Legal Assistant."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API Configuration
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"

    # Local Embedding Configuration (no API limits!)
    use_local_embeddings: bool = False  # Set to True to use local models
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, high-quality
    # Alternative models:
    # - "sentence-transformers/all-mpnet-base-v2" (better quality, slower)
    # - "BAAI/bge-small-en-v1.5" (good for legal/technical text)
    # - "thenlper/gte-base" (high quality general purpose)

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
    max_output_tokens: int = 65536  # Increased for batch analysis (Gemini 2.0 supports up to 65k)
    top_p: float = 0.95
    top_k: int = 40

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 3  # Number of relevant policies to retrieve

    # Regional Knowledge Base Configuration
    regional_kb_enabled: bool = True  # Enable/disable regional KB system
    regional_global_weight: float = 1.1  # Multiplier for global policy scores
    geoip_db_path: str = "./geolite2/GeoLite2-Country.mmdb"  # GeoIP database path

    # Batch Processing Configuration
    batch_mode: bool = True  # Enable batch processing by default
    max_batch_size: int = 50  # Maximum clauses per batch
    batch_chunk_threshold: int = 900000  # Token threshold for chunking
    rate_limit_retry_attempts: int = 3  # Retry attempts for rate limits
    requests_per_minute: int = 15  # RPM limit for free tier
    requests_per_day: int = 250  # Daily quota for free tier

    # Embedding API Rate Limiting (Gemini Embedding API limits)
    # FREE TIER: 100 RPM, 1,000 RPD, 30,000 TPM
    # PAID TIER 1: 3,000 RPM, unlimited RPD, 1M TPM
    embedding_batch_size: int = 50  # Process embeddings in batches of N chunks
    embedding_delay_seconds: float = 1.0  # Delay between embedding batches
    embedding_requests_per_minute: int = 100  # Gemini FREE tier: 100 RPM (paid: 3,000)

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


# Regional Knowledge Base Configuration
# Maps region codes to their configuration
REGION_CONFIG: Dict[str, Dict[str, Any]] = {
    "dubai_uae": {
        "collection_name": "policies_dubai_uae",
        "data_directory": str(Path("data/regional/dubai_uae")),
        "countries": ["AE"],  # United Arab Emirates ISO code
        "enabled": True,
        "metadata": {
            "region_name": "Dubai, UAE",
            "legal_jurisdiction": "UAE Federal Law + DIFC",
            "language": "en"
        }
    },
    # Example future region (disabled):
    # "singapore": {
    #     "collection_name": "policies_singapore",
    #     "data_directory": str(Path("data/regional/singapore")),
    #     "countries": ["SG"],
    #     "enabled": False,
    #     "metadata": {
    #         "region_name": "Singapore",
    #         "legal_jurisdiction": "Singapore Law",
    #         "language": "en"
    #     }
    # }
}


def get_region_for_country(country_code: str) -> Optional[str]:
    """
    Get region code for a given ISO country code.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "AE", "SG", "US")

    Returns:
        Region code (e.g., "dubai_uae") if country is mapped to an enabled region,
        None otherwise.

    Example:
        >>> get_region_for_country("AE")
        "dubai_uae"
        >>> get_region_for_country("US")
        None
    """
    if not country_code:
        return None

    for region_code, config in REGION_CONFIG.items():
        if config.get("enabled", False) and country_code in config.get("countries", []):
            return region_code

    return None


def get_enabled_regions() -> List[str]:
    """
    Get list of enabled region codes.

    Returns:
        List of region codes that are currently enabled.

    Example:
        >>> get_enabled_regions()
        ["dubai_uae"]
    """
    return [
        region_code
        for region_code, config in REGION_CONFIG.items()
        if config.get("enabled", False)
    ]
