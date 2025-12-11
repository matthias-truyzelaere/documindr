"""Chat model provider with caching."""

from functools import lru_cache

from langchain_ollama import ChatOllama

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOllama:
    """Get cached chat model instance with optional API key authentication."""
    headers = (
        {"Authorization": f"Bearer {settings.ollama_api_key}"}
        if settings.ollama_api_key
        else None
    )
    return ChatOllama(
        model=settings.chat_model,
        base_url=settings.ollama_base_url,
        reasoning="low",
        temperature=0.2,
        keep_alive=settings.keep_alive,
        client_kwargs={"headers": headers} if headers else {},
    )
