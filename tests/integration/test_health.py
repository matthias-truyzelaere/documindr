"""Integration tests for health check endpoint."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routes.health.get_chat_model")
def test_health_endpoint(mock_get_chat_model):
    """
    Test health endpoint returns correct status information.

    Verifies:
    - Endpoint returns 200 status code
    - Response success flag is True
    - Response includes correct status code
    - Response includes health status message
    - Response data contains overall status

    The health endpoint checks:
    - Ollama service connectivity (mocked)
    - Database connectivity
    - Connection pool statistics
    """
    # Mock Ollama model to simulate healthy service
    mock_model = MagicMock()
    mock_model.invoke.return_value = "pong"
    mock_get_chat_model.return_value = mock_model

    # Send health check request
    response = client.get("/api/health")

    # Verify response status
    assert response.status_code == 200

    # Parse response data
    data = response.json()

    # Verify response structure and content
    assert data["success"] is True
    assert data["code"] == "HEALTH_OK"
    assert data["message"] == "Service is healthy"
    assert data["data"]["status"] == "healthy"
