"""Base schema definitions for API models."""

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    """Base schema class with common configuration for all API schemas."""

    model_config = ConfigDict(from_attributes=True)
