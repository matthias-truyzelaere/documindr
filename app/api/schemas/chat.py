"""Chat and summary schema definitions."""

from enum import Enum

from pydantic import Field

from app.api.schemas.base import Schema


class SummaryLength(str, Enum):
    """Enumeration of available summary length options."""

    CONCISE = "concise"
    NORMAL = "normal"
    COMPREHENSIVE = "comprehensive"


class ChatRequest(Schema):
    """Schema for chat request with message validation."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["What is the main topic of the document?"],
    )
