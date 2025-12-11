"""Document management endpoints for listing and deletion."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.documents import DocumentItem, DocumentsListResponse
from app.api.schemas.response import APIResponse
from app.infra.database.queries import delete_document_by_id, list_all_documents

router = APIRouter(prefix="/api/documents", tags=["Document Endpoints"])


@router.get("", response_model=APIResponse[DocumentsListResponse])
async def list_documents() -> APIResponse[DocumentsListResponse]:
    """Retrieve all indexed documents with metadata."""
    docs = list_all_documents()
    items: List[DocumentItem] = []
    for d in docs:
        items.append(
            DocumentItem(
                id=d["id"],
                filename=d["filename"],
                file_type=d["file_type"],
                file_size=d["file_size"],
                status=d["status"],
                created_at=d["created_at"],
            )
        )
    return APIResponse(
        success=True,
        code="DOCUMENTS_LIST_SUCCESS",
        message="Documents retrieved successfully",
        data=DocumentsListResponse(documents=items, total=len(items)),
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> APIResponse[None]:
    """Delete document and all associated chunks by ID."""
    deleted = delete_document_by_id(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document with id {document_id} not found.",
            },
        )
    return APIResponse(
        success=True,
        code="DOCUMENT_DELETED",
        message="Document deleted successfully",
        data=None,
    )
