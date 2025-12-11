"""Chat endpoint with streaming RAG responses."""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.schemas.chat import ChatRequest, SummaryLength
from app.domain.rag.streaming import stream_rag, stream_summary
from app.infra.database.queries import document_exists

router = APIRouter(prefix="/api/chat", tags=["Chat Endpoints"])


async def _stream(query: str, document_id: str | None = None):
    """Stream response chunks as UTF-8 encoded bytes."""
    for chunk in stream_rag(query, document_id=document_id):
        yield chunk.encode("utf-8")


async def _stream_summary(document_id: str, length: SummaryLength):
    """Stream summary response chunks as UTF-8 encoded bytes."""
    for chunk in stream_summary(document_id, length):
        yield chunk.encode("utf-8")


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Process chat query with RAG and stream response across all documents.

    Validates input, checks for dangerous patterns, retrieves relevant
    chunks from all indexed documents, and streams LLM response back to client.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CHAT_EMPTY_MESSAGE",
                "message": "Message cannot be empty.",
            },
        )

    dangerous_patterns = ["<script", "javascript:", "onerror="]
    message_lower = request.message.lower()
    if any(pattern in message_lower for pattern in dangerous_patterns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CHAT_INVALID_INPUT",
                "message": "Invalid characters in message.",
            },
        )

    return StreamingResponse(
        _stream(request.message),
        media_type="text/plain",
        headers={"X-Request-Timeout": "300"},
    )


@router.post("/{document_id}")
async def chat_with_document(
    document_id: str, request: ChatRequest
) -> StreamingResponse:
    """
    Process chat query with RAG and stream response for a specific document.

    Only retrieves and uses context from the specified document.
    Validates input, checks for dangerous patterns, retrieves relevant
    chunks from the specified document, and streams LLM response back to client.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CHAT_EMPTY_MESSAGE",
                "message": "Message cannot be empty.",
            },
        )

    dangerous_patterns = ["<script", "javascript:", "onerror="]
    message_lower = request.message.lower()
    if any(pattern in message_lower for pattern in dangerous_patterns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CHAT_INVALID_INPUT",
                "message": "Invalid characters in message.",
            },
        )

    # Verify document exists
    if not document_exists(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document with id {document_id} not found.",
            },
        )

    return StreamingResponse(
        _stream(request.message, document_id=document_id),
        media_type="text/plain",
        headers={"X-Request-Timeout": "300"},
    )


@router.post("/{document_id}/summary")
async def summarize_document(
    document_id: str,
    length: SummaryLength = Query(
        SummaryLength.NORMAL,
        description="Summary length: concise (short), normal (medium), or comprehensive (detailed)",
    ),
) -> StreamingResponse:
    """
    Generate a summary of a specific document.

    Retrieves all chunks from the document and generates a streaming summary
    with the specified length (concise, normal, or comprehensive).
    """
    # Verify document exists
    if not document_exists(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": f"Document with id {document_id} not found.",
            },
        )

    return StreamingResponse(
        _stream_summary(document_id, length),
        media_type="text/plain",
        headers={"X-Request-Timeout": "300"},
    )
