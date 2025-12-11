"""Generic API response and error schema definitions."""

from typing import Generic, Optional, TypeVar

from app.api.schemas.base import Schema

T = TypeVar("T")


class APIResponse(Schema, Generic[T]):
    """Generic API response wrapper with success status and optional data payload."""

    success: bool
    code: str
    message: str
    data: Optional[T] = None


class APIError(Schema):
    """Schema for API error responses."""

    code: str
    message: str
