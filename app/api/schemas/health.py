"""Health check schema definitions."""

from typing import Optional

from app.api.schemas.base import Schema


class HealthResponse(Schema):
    """Schema for health check endpoint response."""

    status: str
    ollama: str
    database: str
    pool_size: Optional[int] = None
    pool_available: Optional[int] = None
