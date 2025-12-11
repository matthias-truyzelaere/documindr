"""Streaming response generation for RAG and summarization."""

import os
import time
from typing import Generator

from app.api.schemas.chat import SummaryLength
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domain.rag.model import get_chat_model
from app.domain.rag.prompts import get_rag_chat_template, get_summary_template
from app.domain.rag.retrieval import (
    build_context,
    extract_sources,
    fix_percent_spacing,
    get_all_document_chunks,
    hybrid_search,
)

logger = get_logger(__name__)
settings = get_settings()


def format_sources(sources: list[str]) -> str:
    """
    Format sources to show only filename and chunk info.

    Args:
        sources: List of source strings in format "path:page:chunk"

    Returns:
        Comma-separated formatted sources with filename only

    Example:
        ["/data/doc.pdf:1:0", "/data/doc.pdf:2:1"]
        -> "doc.pdf:1:0, doc.pdf:2:1"
    """
    formatted = []
    for source in sources:
        parts = source.split(":")
        if len(parts) >= 3:
            filename = os.path.basename(parts[0])
            formatted.append(f"{filename}:{parts[1]}:{parts[2]}")
        else:
            filename = os.path.basename(source)
            formatted.append(filename)
    return ", ".join(formatted)


def stream_rag(
    query: str, k: int | None = None, document_id: str | None = None
) -> Generator[str, None, None]:
    """
    Stream RAG response chunks with retrieval and generation metrics.

    Performs hybrid search, builds context, and streams LLM response
    while logging performance metrics (TTFT, tokens/sec).

    Args:
        query: User question
        k: Number of chunks to retrieve (defaults to settings.retriever_k)
        document_id: Optional document ID to limit search to specific document

    Yields:
        Text chunks from LLM response
    """
    if k is None:
        k = settings.retriever_k

    model = get_chat_model()

    # Perform hybrid search
    results = hybrid_search(query, k, document_id)

    if not results:
        logger.info(f"Query received: {query[:100]}... | No results found")
        yield "I cannot find this information in the provided text."
        return

    # Extract and format sources
    sources = extract_sources(results)
    formatted_sources = format_sources(sources)

    # Log query with sources
    truncated_query = query[:100] + ("..." if len(query) > 100 else "")
    logger.info(f"Query received: {truncated_query}")
    logger.info(f"Sources: [{formatted_sources}]")

    # Build context and prompt
    context = build_context(results)
    prompt_template = get_rag_chat_template()
    prompt = prompt_template.format(context=context, query=query)

    # Stream LLM response and track metrics
    start = time.perf_counter()
    first = None
    total = 0
    ttft = 0.0

    for chunk in model.stream(prompt):
        text = getattr(chunk, "content", None)
        if not text:
            continue
        now = time.perf_counter()
        if first is None:
            first = now
            ttft = first - start
        total += len(text)
        if total == len(text):
            text = text.lstrip("\n\r ")
        yield fix_percent_spacing(text)

    # Calculate and log final metrics
    end = time.perf_counter()
    llm_time = end - start
    gen_phase = end - first if first else llm_time
    tps = total / gen_phase if gen_phase > 0 else 0.0

    logger.info(
        f"LLM Response Time: {llm_time:.2f}s | First Token: {ttft:.2f}s | Tokens Per Second: {tps:.1f}"
    )


def stream_summary(
    document_id: str, length: SummaryLength
) -> Generator[str, None, None]:
    """
    Stream document summary with specified length.

    Retrieves all chunks from the document and generates a streaming summary
    with the specified length (concise, normal, or comprehensive).

    Args:
        document_id: Document ID to summarize
        length: Summary length (concise, normal, or comprehensive)

    Yields:
        Text chunks from summary generation
    """
    model = get_chat_model()

    # Retrieve all document chunks
    chunks = get_all_document_chunks(document_id)

    logger.info(
        f"Summary request: Document ID={document_id} | Length={length.value} | Chunks={len(chunks)}"
    )

    if not chunks:
        logger.info(f"No chunks found for document: {document_id}")
        yield "Unable to generate summary: no content found for this document."
        return

    # Build context and prompt
    context = build_context(chunks)
    summary_template = get_summary_template(length)
    prompt = summary_template.format(context=context)

    # Stream summary and track metrics
    start = time.perf_counter()
    first = None
    total = 0
    ttft = 0.0

    for chunk in model.stream(prompt):
        text = getattr(chunk, "content", None)
        if not text:
            continue
        now = time.perf_counter()
        if first is None:
            first = now
            ttft = first - start
        total += len(text)
        if total == len(text):
            text = text.lstrip("\n\r ")
        yield fix_percent_spacing(text)

    # Calculate and log final metrics
    end = time.perf_counter()
    llm_time = end - start
    gen_phase = end - first if first else llm_time
    tps = total / gen_phase if gen_phase > 0 else 0.0

    logger.info(
        f"LLM Response Time: {llm_time:.2f}s | First Token: {ttft:.2f}s | Tokens Per Second: {tps:.1f}"
    )
