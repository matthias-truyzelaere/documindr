"""Integration tests for chat endpoints with RAG functionality."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def fake_stream_rag(query, document_id=None):
    """
    Mock stream_rag function for testing.

    Simulates streaming response behavior by yielding text chunks.
    Includes document_id in response when provided.

    Args:
        query: User query string (unused in mock)
        document_id: Optional document ID to include in response

    Yields:
        Text chunks simulating streaming response
    """
    if document_id:
        yield f"Document {document_id}: "
    yield "Hello"
    yield " world"


def test_chat_endpoint():
    """
    Test chat endpoint returns streaming response across all documents.

    Verifies:
    - Endpoint returns 200 status code
    - Response contains expected text chunks
    - Streaming behavior works correctly
    """
    # Patch where stream_rag is imported in the route file
    with patch("app.api.routes.chat.stream_rag", side_effect=fake_stream_rag):
        response = client.post("/api/chat", json={"message": "Hi"})

        assert response.status_code == 200
        text = response.text
        assert "Hello" in text
        assert "world" in text


def test_chat_with_document_endpoint(test_document_id):
    """
    Test chat endpoint with specific document ID returns filtered response.

    Verifies:
    - Endpoint validates document exists
    - Returns 200 status code
    - Response includes document ID
    - Response contains expected text chunks
    """
    # Patch both document_exists and stream_rag at their import locations
    with (
        patch("app.api.routes.chat.document_exists", return_value=True),
        patch("app.api.routes.chat.stream_rag", side_effect=fake_stream_rag),
    ):
        response = client.post(f"/api/chat/{test_document_id}", json={"message": "Hi"})

        assert response.status_code == 200
        text = response.text
        assert test_document_id in text
        assert "Hello" in text
        assert "world" in text


def test_chat_with_nonexistent_document(nonexistent_document_id):
    """
    Test chat endpoint returns 404 for nonexistent document.

    Verifies:
    - Endpoint validates document existence
    - Returns 404 status code
    - Error response includes correct error code
    """
    with patch("app.api.routes.chat.document_exists", return_value=False):
        response = client.post(
            f"/api/chat/{nonexistent_document_id}", json={"message": "Hi"}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "DOCUMENT_NOT_FOUND"
