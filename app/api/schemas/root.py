"""Root endpoint schema definitions."""

from app.api.schemas.base import Schema


class RootResponse(Schema):
    """Schema for root endpoint response with API metadata."""

    status: str
    version: str
    author: str
