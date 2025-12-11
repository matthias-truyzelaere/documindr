"""CORS middleware configuration for FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware with allowed origins from settings."""
    settings = get_settings()
    raw = settings.allowed_origins or ""
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
