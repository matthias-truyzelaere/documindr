"""Document retrieval using hybrid search (semantic + BM25)."""

import os
import re
from typing import List

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from pgvector.psycopg import Vector, register_vector

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domain.embeddings.provider import get_embedding_function
from app.infra.database.connection import pool

logger = get_logger(__name__)
settings = get_settings()


def fix_percent_spacing(text: str) -> str:
    """Fix spacing around percentage symbols (e.g., '50 %' -> '50%')."""
    return re.sub(r"(\d+)\s+%", r"\1%", text)


def semantic_search(
    query: str, k: int, document_id: str | None = None
) -> List[Document]:
    """Search for documents using vector similarity."""
    embed = get_embedding_function()
    vector = Vector(embed.embed_query(query))

    with pool.connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            if document_id:
                # Search only within specific document
                cur.execute(
                    """
                    SELECT id, document_id, chunk_index, content, metadata
                    FROM document_chunks
                    WHERE document_id = %s
                    ORDER BY embedding <-> %s
                    LIMIT %s
                    """,
                    (document_id, vector, k),
                )
            else:
                # Search across all documents
                cur.execute(
                    """
                    SELECT id, document_id, chunk_index, content, metadata
                    FROM document_chunks
                    ORDER BY embedding <-> %s
                    LIMIT %s
                    """,
                    (vector, k),
                )
            rows = cur.fetchall()

    results: List[Document] = []
    for chunk_id, doc_id, idx, content, metadata in rows:
        m = metadata or {}
        m["id"] = chunk_id
        m["document_id"] = doc_id
        m["chunk_index"] = idx
        results.append(Document(page_content=content, metadata=m))
    return results


def get_all_document_chunks(document_id: str) -> List[Document]:
    """Retrieve all chunks for a specific document ordered by chunk index."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, document_id, chunk_index, content, metadata
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index ASC
                """,
                (document_id,),
            )
            rows = cur.fetchall()

    results: List[Document] = []
    for chunk_id, doc_id, idx, content, metadata in rows:
        m = metadata or {}
        m["id"] = chunk_id
        m["document_id"] = doc_id
        m["chunk_index"] = idx
        results.append(Document(page_content=content, metadata=m))
    return results


def hybrid_search(query: str, k: int, document_id: str | None = None) -> List[Document]:
    """Combine semantic search with BM25 for better retrieval."""
    semantic = semantic_search(query, k, document_id)
    if not semantic:
        return []
    return BM25Retriever.from_documents(semantic, k=k).invoke(query)


def build_context(chunks: List[Document]) -> str:
    """Format retrieved chunks into a single context string."""
    parts = []
    for i, doc in enumerate(chunks, 1):
        parts.append(f"[Chunk {i}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def extract_sources(chunks: List[Document]) -> List[str]:
    """Extract source references from chunk metadata."""
    out: List[str] = []
    for meta in [c.metadata or {} for c in chunks]:
        source = meta.get("source", "")
        page = meta.get("page", 0)
        idx = meta.get("chunkIndex", 0)
        name = os.path.basename(str(source)) if source else "unknown"
        try:
            page = int(page)
        except Exception:
            page = 0
        try:
            idx = int(idx)
        except Exception:
            idx = 0
        out.append(f"{name}:{page}:{idx}")
    return out
