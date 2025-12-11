"""Integration tests for API root endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """
    Test API root endpoint returns version and status information.

    Verifies:
    - Endpoint returns 200 status code
    - Response success flag is True
    - Response includes correct status code
    - Response includes ready message
    - Response data contains all required fields:
        - status: API operational status
        - version: API version number
        - author: API author information

    This endpoint provides basic API metadata and serves as
    a simple connectivity test.
    """
    # Send request to root endpoint
    response = client.get("/api")

    # Verify response status
    assert response.status_code == 200

    # Parse response body
    body = response.json()

    # Verify response metadata
    assert body["success"] is True
    assert body["code"] == "API_READY"
    assert body["message"] == "API is ready"

    # Verify response data contains required fields
    data = body["data"]
    assert "status" in data
    assert "version" in data
    assert "author" in data
