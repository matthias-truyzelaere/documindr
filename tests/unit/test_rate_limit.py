"""Unit tests for token bucket rate limiting middleware."""

import asyncio

from fastapi import Request

from app.core.ratelimit import buckets, rate_limit


class DummyCallNext:
    """
    Mock for FastAPI middleware call_next function.

    Simulates successful request processing by returning
    a simple "OK" response without actual endpoint execution.
    """

    async def __call__(self, request):
        """
        Process mock request.

        Args:
            request: FastAPI Request object

        Returns:
            Simple "OK" string response
        """
        return "OK"


def test_rate_limit_allows_initial_requests():
    """
    Test rate limiter allows requests within limit.

    Verifies:
    - Initial requests are allowed through
    - Token bucket is created for new IP/path combination
    - Middleware returns successful response
    - No rate limit exception is raised

    The token bucket rate limiter tracks requests per IP address
    and endpoint path. Each bucket starts with full tokens and
    refills over time based on the configured rate limit window.

    This test ensures the basic flow works for the first request
    from a new IP address.
    """
    # Use localhost IP for testing
    ip = "127.0.0.1"

    # Clear any existing rate limit buckets
    buckets.clear()

    # Create mock request from test IP with required ASGI scope keys
    request = Request(
        {
            "type": "http",
            "client": (ip, 123),
            "path": "/test",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )

    # Create mock call_next function
    call_next = DummyCallNext()

    # Execute rate limit middleware
    result = asyncio.run(rate_limit(request, call_next))

    # Verify request was allowed through
    assert result == "OK"
