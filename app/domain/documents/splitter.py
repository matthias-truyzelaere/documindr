"""Document splitting with adaptive chunk sizing."""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings

settings = get_settings()

BASE_CHUNK = settings.chunk_size
MIN_CHARS = settings.chunk_size_min
OVERLAP = settings.chunk_overlap


def choose_chunk_size(length: int, base: int = BASE_CHUNK) -> int:
    """
    Dynamically adjust chunk size based on document length.

    Smaller documents use smaller chunks to avoid over-chunking,
    larger documents use reduced chunk size for better granularity.
    """
    if length < 2000:
        return max(int(base * 0.8), 300)
    if length < 10000:
        return base
    return max(int(base * 0.6), 400)


def split_documents(
    docs: List[Document],
    base_chunk_size: int = BASE_CHUNK,
    overlap: int = OVERLAP,
    min_chars: int = MIN_CHARS,
) -> List[Document]:
    """
    Split documents into chunks with adaptive sizing.

    Filters out chunks below min_chars, adjusts chunk size based on
    document length, and uses semantic separators for better splits.
    """
    if not docs:
        return []

    filtered: List[Document] = []
    for d in docs:
        text = (d.page_content or "").strip()
        if len(text) >= min_chars:
            d.page_content = text
            filtered.append(d)

    if not filtered:
        return []

    out: List[Document] = []

    for doc in filtered:
        text = doc.page_content or ""
        size = choose_chunk_size(len(text), base_chunk_size)

        if len(text) <= size * 0.8:
            out.append(doc)
            continue

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            length_function=len,
            separators=[
                "\n\n## ",
                "\n\n### ",
                "\n\n",
                "\n",
                ". ",
                "! ",
                "? ",
                "; ",
                ", ",
                " ",
                "",
            ],
            is_separator_regex=False,
        )

        out.extend(splitter.split_documents([doc]))

    return out
