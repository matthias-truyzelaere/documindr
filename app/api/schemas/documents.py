"""Document-related schema definitions."""

from datetime import datetime
from typing import List

from app.api.schemas.base import Schema


class DocumentItem(Schema):
    """Schema representing a single document item."""

    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime


class DocumentsListResponse(Schema):
    """Schema for document list response with pagination info."""

    documents: List[DocumentItem]
    total: int
