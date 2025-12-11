"""Integration tests for document upload endpoint."""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.domain.uploads.processor.index_chunks", return_value=("docid", 5))
@patch("app.domain.uploads.processor.load_document", return_value=[])
def test_upload_endpoint(mock_load, mock_index, tmp_path):
    """
    Test document upload endpoint processes file successfully.

    Verifies:
    - Endpoint accepts multipart file upload
    - Returns 200 status code
    - Response success flag is True
    - Response includes correct status code
    - Response message indicates successful indexing
    - Response data contains:
        - filename: Original filename
        - document_id: Generated document UUID
        - chunks_indexed: Number of chunks created

    Mocks:
    - load_document: Returns empty list to skip actual document loading
    - index_chunks: Returns mock document_id and chunk count

    Args:
        mock_load: Mock for document loading
        mock_index: Mock for chunk indexing
        tmp_path: Pytest fixture for temporary directory
    """
    # Create temporary upload directory
    fake_dir = tmp_path / "uploads"
    fake_dir.mkdir()

    # Patch upload directory to use temporary path
    with patch("app.domain.uploads.processor.BASE_UPLOAD_DIR", fake_dir):
        # Create fake PDF file content
        file_content = io.BytesIO(b"dummy pdf content")

        # Send upload request with multipart form data
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", file_content, "application/pdf")},
        )

        # Verify response status
        assert response.status_code == 200

        # Parse response body
        body = response.json()

        # Verify response metadata
        assert body["success"] is True
        assert body["code"] == "UPLOAD_SUCCESS"
        assert "indexed successfully" in body["message"]

        # Verify response data
        data = body["data"]
        assert data["filename"] == "test.pdf"
        assert data["document_id"] == "docid"
        assert data["chunks_indexed"] == 5
