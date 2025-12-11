"""Document loading for various file formats."""

import os
from typing import List

from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader
from pypdf import PdfReader
from unstructured.cleaners.core import clean_extra_whitespace

from app.core.logger import get_logger

logger = get_logger(__name__)


def load_pdf(path: str) -> List[Document]:
    """Extract text from PDF files page by page."""
    name = os.path.basename(path)
    reader = PdfReader(path)
    docs: List[Document] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        text = text.strip()
        if len(text) < 10:
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": path,
                    "page": i + 1,
                    "category": "PDFPage",
                    "filename": name,
                },
            )
        )
    return docs


def load_document(path: str) -> List[Document]:
    """
    Load document based on file extension.

    Uses pypdf for PDFs (faster), unstructured for other formats.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return load_pdf(path)

    loader = UnstructuredLoader(
        file_path=path,
        post_processors=[clean_extra_whitespace],
    )
    try:
        return loader.load()
    except Exception as e:
        name = os.path.basename(path)
        logger.error(f"Failed to load {name}", exc_info=e)
        raise
