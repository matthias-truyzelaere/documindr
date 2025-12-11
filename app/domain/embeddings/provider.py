"""Embedding model provider with warmup and caching."""

from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_warmed_up = False


@lru_cache(maxsize=1)
def get_embedding_function() -> OllamaEmbeddings:
    """
    Get cached embedding model instance.

    Warms up the model on first call to reduce latency on
    subsequent embedding requests.
    """
    global _warmed_up
    model = settings.embedding_model
    base_url = settings.ollama_base_url
    keep_alive = settings.keep_alive

    try:
        embeddings = OllamaEmbeddings(
            model=model,
            base_url=base_url,
            keep_alive=keep_alive,
        )

        if not _warmed_up:
            embeddings.embed_query("warmup")
            _warmed_up = True
            logger.info(f"Embedding model {model} warmed up successfully")

        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}")
        raise EmbeddingError(f"Failed to initialize embedding model: {e}")
