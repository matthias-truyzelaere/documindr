"""FastAPI application entry point with middleware and error handlers."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router
from app.api.routes.upload import router as upload_router
from app.api.schemas.response import APIError
from app.core.cors import configure_cors
from app.core.logger import get_logger, setup_logger
from app.core.ratelimit import rate_limit
from app.infra.database.connection import close_pool

setup_logger()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and graceful shutdown."""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown - waiting for requests...")
    await asyncio.sleep(2)
    close_pool()


app = FastAPI(
    title="RAG API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={"useCdn": False},
)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Enforce global request size limit (210MB)."""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 210 * 1024 * 1024:
            return JSONResponse(
                status_code=413,
                content={"code": "PAYLOAD_TOO_LARGE", "message": "Request too large"},
            )
    return await call_next(request)


app.middleware("http")(rate_limit)

configure_cors(app)

app.include_router(root_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(health_router)
app.include_router(documents_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to consistent APIError format."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = APIError(code=detail["code"], message=detail["message"])
    else:
        error = APIError(code="HTTP_ERROR", message=str(detail))

    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """Convert validation errors to consistent APIError format."""
    error = APIError(code="VALIDATION_ERROR", message=str(exc))
    return JSONResponse(
        status_code=422,
        content=error.model_dump(),
    )
