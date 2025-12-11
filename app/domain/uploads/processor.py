"""File upload processing with validation and indexing."""

import re
from pathlib import Path
from typing import List, Tuple

import aiofiles
from fastapi import UploadFile
from langchain_core.documents import Document

from app.core.config import get_settings
from app.core.exceptions import (
    DocumentProcessingError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from app.core.logger import get_logger
from app.domain.documents.hashing import compute_file_hash
from app.domain.documents.loader import load_document
from app.domain.documents.splitter import split_documents
from app.infra.database.queries import index_chunks

logger = get_logger(__name__)
settings = get_settings()

ALLOWED_EXT = {".txt", ".rtf", ".doc", ".docx", ".pdf", ".ppt", ".pptx"}

BASE_UPLOAD_DIR = Path(settings.data_path)
MAX_FILE_SIZE = settings.max_file_size


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def validate_extension(name: str) -> bool:
    """Check if file extension is allowed."""
    return Path(name).suffix.lower() in ALLOWED_EXT


def sanitize_filename(name: str) -> str:
    """Remove dangerous characters from filename."""
    name = name.strip()
    name = name.replace("..", "")
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = re.sub(r"[^\w\s.-]", "", name)
    name = name[:255]
    return name


async def save_upload(file: UploadFile) -> Path:
    """Save uploaded file to disk asynchronously."""
    ensure_dir(BASE_UPLOAD_DIR)
    sanitized_name = sanitize_filename(file.filename)
    dest = BASE_UPLOAD_DIR / sanitized_name

    content = await file.read()
    async with aiofiles.open(dest, "wb") as buffer:
        await buffer.write(content)

    return dest


async def process_upload(file: UploadFile) -> Tuple[str, int, str]:
    """
    Process uploaded file: validate, save, chunk, embed, and index.

    Returns (document_id, chunks_indexed, filename). If file already
    exists (based on hash), returns existing ID with 0 chunks indexed.
    """
    if not file.filename:
        raise InvalidFileTypeError("Filename is required.")

    sanitized_filename = sanitize_filename(file.filename)

    if not validate_extension(sanitized_filename):
        allowed = ", ".join(sorted(ALLOWED_EXT))
        raise InvalidFileTypeError(
            f"Only files with extensions {allowed} are supported."
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise FileTooLargeError(
            f"File size exceeds maximum allowed size of {max_mb:.1f} MB."
        )

    if file_size == 0:
        raise InvalidFileTypeError("File is empty.")

    try:
        path = await save_upload(file)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise DocumentProcessingError(f"Failed to save uploaded file: {e}")

    try:
        filename = sanitized_filename
        file_type = Path(filename).suffix.lower().lstrip(".") or "unknown"
        actual_file_size = path.stat().st_size
        content_hash = compute_file_hash(str(path))

        docs: List[Document] = load_document(str(path))
        chunks = split_documents(docs)

        document_id, count = index_chunks(
            filename=filename,
            file_type=file_type,
            file_size=actual_file_size,
            content_hash=content_hash,
            chunks=chunks,
        )

        if count == 0:
            logger.info(
                "Skipped indexing %s (already indexed as document %s)",
                filename,
                document_id,
            )
        else:
            logger.info("Indexed %s with %d chunks", filename, len(chunks))

        return document_id, count, filename
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise DocumentProcessingError(f"Failed to process document: {e}")
