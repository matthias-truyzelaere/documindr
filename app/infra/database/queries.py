"""Database queries for document and chunk management."""

import json
import time
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

from langchain_core.documents import Document

from app.core.exceptions import DatabaseError, EmbeddingError
from app.core.logger import get_logger
from app.domain.embeddings.provider import get_embedding_function
from app.infra.database.connection import pool

logger = get_logger(__name__)


def get_document_by_hash(content_hash: str) -> Optional[str]:
    """Check if document with given hash already exists."""
    query = "SELECT id FROM documents WHERE content_hash = %s"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (content_hash,))
                row = cur.fetchone()
        return str(row[0]) if row else None
    except Exception as e:
        logger.error(f"Database error in get_document_by_hash: {e}")
        raise DatabaseError(f"Failed to query document by hash: {e}")


def document_exists(document_id: str) -> bool:
    """Check if document with given ID exists."""
    query = "SELECT EXISTS(SELECT 1 FROM documents WHERE id = %s)"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (document_id,))
                row = cur.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
        logger.error(f"Database error in document_exists: {e}")
        raise DatabaseError(f"Failed to check document existence: {e}")


def insert_document(
    filename: str,
    file_type: str,
    file_size: int,
    content_hash: str,
) -> str:
    """Create a new document record with processing status."""
    document_id = str(uuid.uuid4())
    query = """
        INSERT INTO documents (id, filename, file_type, file_size, content_hash, status)
        VALUES (%s, %s, %s, %s, %s, 'processing')
    """
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (document_id, filename, file_type, file_size, content_hash),
                )
            conn.commit()
        return document_id
    except Exception as e:
        logger.error(f"Database error in insert_document: {e}")
        raise DatabaseError(f"Failed to insert document: {e}")


def insert_document_chunks(
    document_id: str,
    chunks: Iterable[Document],
    embeddings: List[List[float]],
) -> int:
    """Insert document chunks with their embeddings into the database."""
    rows: List[Tuple] = []
    for chunk_index, (document, embedding) in enumerate(zip(chunks, embeddings)):
        id = str(uuid.uuid4())
        metadata = document.metadata or {}
        metadata["chunk_index"] = chunk_index
        rows.append(
            (
                id,
                document_id,
                chunk_index,
                document.page_content or "",
                embedding,
                json.dumps(metadata),
            )
        )
    query = """
        INSERT INTO document_chunks (id, document_id, chunk_index, content, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, rows)
            conn.commit()
        return len(rows)
    except Exception as e:
        logger.error(f"Database error in insert_document_chunks: {e}")
        raise DatabaseError(f"Failed to insert document chunks: {e}")


def mark_document_completed(document_id: str) -> None:
    """Mark document as successfully processed."""
    query = "UPDATE documents SET status = 'completed' WHERE id = %s"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (document_id,))
            conn.commit()
    except Exception as e:
        logger.error(f"Database error in mark_document_completed: {e}")
        raise DatabaseError(f"Failed to mark document as completed: {e}")


def batch_embed(
    texts: List[str], model, batch_size: int = 32, max_retries: int = 3
) -> List[List[float]]:
    """
    Generate embeddings in batches with exponential backoff retry.

    Processes texts in smaller batches to avoid timeouts and retries
    failed batches up to max_retries times with exponential backoff.
    """
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                embeddings.extend(model.embed_documents(batch))
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
    return embeddings


def index_chunks(
    filename: str,
    file_type: str,
    file_size: int,
    content_hash: str,
    chunks: List[Document],
) -> Tuple[str, int]:
    """
    Index document chunks with embeddings.

    Returns (document_id, chunks_indexed). If document already exists
    based on content hash, returns existing ID with 0 chunks indexed.
    """
    existing_id = get_document_by_hash(content_hash)
    if existing_id:
        return existing_id, 0

    document_id = insert_document(filename, file_type, file_size, content_hash)
    try:
        model = get_embedding_function()
        texts = [c.page_content or "" for c in chunks]
        embeddings = batch_embed(texts, model)
    except Exception as e:
        logger.error(f"Embedding error in index_chunks: {e}")
        raise EmbeddingError(f"Failed to generate embeddings: {e}")

    count = insert_document_chunks(document_id, chunks, embeddings)
    mark_document_completed(document_id)
    return document_id, count


def list_all_documents() -> List[Dict]:
    """Retrieve all documents ordered by creation date."""
    query = """
        SELECT id, filename, file_type, file_size, status, created_at
        FROM documents
        ORDER BY created_at DESC
    """
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        results = []
        for row in rows:
            results.append(
                {
                    "id": str(row[0]),
                    "filename": row[1],
                    "file_type": row[2],
                    "file_size": row[3],
                    "status": row[4],
                    "created_at": row[5],
                }
            )
        return results
    except Exception as e:
        logger.error(f"Database error in list_all_documents: {e}")
        raise DatabaseError(f"Failed to list documents: {e}")


def delete_document_by_id(document_id: str) -> bool:
    """Delete document and all associated chunks (cascades automatically)."""
    query = "DELETE FROM documents WHERE id = %s"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (document_id,))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted
    except Exception as e:
        logger.error(f"Database error in delete_document_by_id: {e}")
        raise DatabaseError(f"Failed to delete document: {e}")
