"""Application configuration management using Pydantic settings."""

from functools import lru_cache

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    allowed_origins: str

    ollama_base_url: str
    ollama_api_key: str | None = None
    chat_model: str
    embedding_model: str
    keep_alive: int

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str

    chunk_size: int
    chunk_size_min: int
    chunk_overlap: int
    retriever_k: int

    data_path: str
    max_file_size: int

    rate_limit_chat: int
    rate_limit_chat_window: int
    rate_limit_upload: int
    rate_limit_upload_window: int
    rate_limit_default: int
    rate_limit_default_window: int

    @field_validator(
        "postgres_user", "postgres_password", "postgres_db", "postgres_host"
    )
    def validate_required(cls, v):
        """Ensure required database fields are not empty."""
        if not v:
            raise ValueError("Required database configuration missing")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()
