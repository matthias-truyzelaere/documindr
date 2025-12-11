"""Upload-related schema definitions."""

from typing import Optional

from app.api.schemas.base import Schema


class UploadResponse(Schema):
    """Schema for document upload response."""

    filename: str
    document_id: Optional[str] = None
    chunks_indexed: Optional[int] = None
