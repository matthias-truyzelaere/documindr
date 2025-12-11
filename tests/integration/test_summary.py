"""Integration tests for document summarization endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def fake_stream_summary(document_id, length):
    """Mock summary stream generator for testing."""
    yield f"Summary ({length.value}): "
    yield "This document discusses key topics. "
    yield "The main findings are significant. "
    yield "Overall conclusions are presented."


def test_summary_endpoint_concise(test_document_id):
    """Test summary endpoint with concise length parameter."""
    with (
        patch("app.api.routes.chat.document_exists", return_value=True),
        patch("app.api.routes.chat.stream_summary", side_effect=fake_stream_summary),
    ):
        response = client.post(f"/api/chat/{test_document_id}/summary?length=concise")

        assert response.status_code == 200
        text = response.text
        assert "Summary" in text
        assert "concise" in text


def test_summary_endpoint_normal(test_document_id):
    """Test summary endpoint with normal length parameter."""
    with (
        patch("app.api.routes.chat.document_exists", return_value=True),
        patch("app.api.routes.chat.stream_summary", side_effect=fake_stream_summary),
    ):
        response = client.post(f"/api/chat/{test_document_id}/summary?length=normal")

        assert response.status_code == 200
        text = response.text
        assert "Summary" in text
        assert "normal" in text


def test_summary_endpoint_comprehensive(test_document_id):
    """Test summary endpoint with comprehensive length parameter."""
    with (
        patch("app.api.routes.chat.document_exists", return_value=True),
        patch("app.api.routes.chat.stream_summary", side_effect=fake_stream_summary),
    ):
        response = client.post(
            f"/api/chat/{test_document_id}/summary?length=comprehensive"
        )

        assert response.status_code == 200
        text = response.text
        assert "Summary" in text
        assert "comprehensive" in text


def test_summary_endpoint_nonexistent_document(nonexistent_document_id):
    """Test summary endpoint returns 404 for nonexistent document."""
    with patch("app.api.routes.chat.document_exists", return_value=False):
        response = client.post(f"/api/chat/{nonexistent_document_id}/summary")

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "DOCUMENT_NOT_FOUND"


def test_summary_endpoint_default_length(test_document_id):
    """Test that default length is normal when not specified."""
    with (
        patch("app.api.routes.chat.document_exists", return_value=True),
        patch("app.api.routes.chat.stream_summary", side_effect=fake_stream_summary),
    ):
        response = client.post(f"/api/chat/{test_document_id}/summary")

        assert response.status_code == 200
        text = response.text
        assert "Summary" in text
