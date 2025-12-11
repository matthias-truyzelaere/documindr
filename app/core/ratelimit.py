"""Token bucket rate limiting middleware."""

import time

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()

RATE_LIMITS = {
    "/api/chat": (settings.rate_limit_chat, settings.rate_limit_chat_window),
    "/api/upload": (settings.rate_limit_upload, settings.rate_limit_upload_window),
}

DEFAULT_RATE_LIMIT = settings.rate_limit_default
DEFAULT_WINDOW = settings.rate_limit_default_window

buckets: dict[str, dict[str, dict[str, float]]] = {}
last_cleanup = time.time()
CLEANUP_INTERVAL = 300


def cleanup_old_buckets():
    """Remove expired rate limit buckets to prevent memory leaks."""
    global last_cleanup
    now = time.time()

    if now - last_cleanup < CLEANUP_INTERVAL:
        return

    for ip in list(buckets.keys()):
        for path in list(buckets[ip].keys()):
            if now - buckets[ip][path]["timestamp"] > DEFAULT_WINDOW * 2:
                del buckets[ip][path]
        if not buckets[ip]:
            del buckets[ip]

    last_cleanup = now


async def rate_limit(request: Request, call_next):
    """Token bucket rate limiter that refills tokens over time."""
    cleanup_old_buckets()

    ip = request.client.host
    path = request.url.path
    now = time.time()

    limit, window = RATE_LIMITS.get(path, (DEFAULT_RATE_LIMIT, DEFAULT_WINDOW))

    if ip not in buckets:
        buckets[ip] = {}

    if path not in buckets[ip]:
        buckets[ip][path] = {"tokens": limit, "timestamp": now}

    bucket = buckets[ip][path]
    elapsed = now - bucket["timestamp"]

    bucket["tokens"] = min(
        limit,
        bucket["tokens"] + elapsed * (limit / window),
    )
    bucket["timestamp"] = now

    if bucket["tokens"] < 1:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Try again soon.",
            },
        )

    bucket["tokens"] -= 1

    return await call_next(request)
