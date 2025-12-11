"""Pytest configuration and shared fixtures for all tests."""

import os
from unittest.mock import MagicMock, patch

import pytest

# Set test environment variables at module import time
_test_env = {
    "POSTGRES_USER": "testuser",
    "POSTGRES_PASSWORD": "testpass",
    "POSTGRES_DB": "testdb",
    "POSTGRES_HOST": "postgres",
    "POSTGRES_PORT": "5432",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_API_KEY": "",
    "CHAT_MODEL": "llama3",
    "EMBEDDING_MODEL": "nomic-embed-text",
    "KEEP_ALIVE": "300",
    "ALLOWED_ORIGINS": "*",
    "CHUNK_SIZE": "800",
    "CHUNK_SIZE_MIN": "100",
    "CHUNK_OVERLAP": "200",
    "RETRIEVER_K": "5",
    "DATA_PATH": "/tmp/data",
    "MAX_FILE_SIZE": "10485760",
    "RATE_LIMIT_CHAT": "10",
    "RATE_LIMIT_CHAT_WINDOW": "60",
    "RATE_LIMIT_UPLOAD": "5",
    "RATE_LIMIT_UPLOAD_WINDOW": "60",
    "RATE_LIMIT_DEFAULT": "20",
    "RATE_LIMIT_DEFAULT_WINDOW": "60",
}

for _key, _value in _test_env.items():
    os.environ[_key] = _value


@pytest.fixture(scope="session", autouse=True)
def mock_ollama_for_all_tests():
    """
    Mock Ollama connections for all tests in the test suite.

    This fixture runs automatically for all tests and mocks:
    - OllamaEmbeddings for embedding generation
    - ChatOllama for chat completions
    """
    with patch("app.domain.embeddings.provider.OllamaEmbeddings") as mock_embeddings:
        mock_embed_instance = MagicMock()
        mock_embed_instance.embed_documents.return_value = [[0.1] * 768]
        mock_embed_instance.embed_query.return_value = [0.1] * 768
        mock_embeddings.return_value = mock_embed_instance

        with patch("app.domain.rag.model.ChatOllama") as mock_chat:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock(
                content="Mocked response"
            )
            mock_chat_instance.stream.return_value = iter(
                ["Mocked ", "streaming ", "response"]
            )
            mock_chat.return_value = mock_chat_instance

            yield


@pytest.fixture
def test_document_id():
    """Provide a valid test document UUID."""
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def nonexistent_document_id():
    """Provide a valid UUID format for nonexistent document tests."""
    return "00000000-0000-0000-0000-000000000000"
