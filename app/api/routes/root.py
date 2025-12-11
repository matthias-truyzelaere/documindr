"""Root API endpoint for version and status information."""

from fastapi import APIRouter

from app.api.schemas.response import APIResponse
from app.api.schemas.root import RootResponse

router = APIRouter(prefix="/api", tags=["Default Endpoints"])


@router.get("", response_model=APIResponse[RootResponse])
async def root() -> APIResponse[RootResponse]:
    """API root endpoint with version info."""
    return APIResponse(
        success=True,
        code="API_READY",
        message="API is ready",
        data=RootResponse(
            status="ready",
            version="1.0.0",
            author="Matthias Truyzelaere",
        ),
    )
