"""Health check endpoint with service status monitoring."""

from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.api.schemas.response import APIResponse
from app.domain.rag.model import get_chat_model
from app.infra.database.connection import pool

router = APIRouter(prefix="/api", tags=["Default Endpoints"])


@router.get("/health", response_model=APIResponse[HealthResponse])
async def health() -> APIResponse[HealthResponse]:
    """Check health of Ollama, database, and connection pool."""
    ollama_status = "healthy"
    db_status = "healthy"

    try:
        model = get_chat_model()
        model.invoke("ping")
    except Exception:
        ollama_status = "unhealthy"

    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    overall_status = (
        "healthy"
        if ollama_status == "healthy" and db_status == "healthy"
        else "unhealthy"
    )

    pool_stats = pool.get_stats()

    return APIResponse(
        success=overall_status == "healthy",
        code="HEALTH_OK" if overall_status == "healthy" else "HEALTH_DEGRADED",
        message=f"Service is {overall_status}",
        data=HealthResponse(
            status=overall_status,
            ollama=ollama_status,
            database=db_status,
            pool_size=pool_stats.get("pool_size", 0),
            pool_available=pool_stats.get("pool_available", 0),
        ),
    )
