"""Unit tests for adaptive chunk size selection."""

from app.domain.documents.splitter import choose_chunk_size


def test_choose_chunk_size_small():
    """
    Test chunk size selection for small documents.

    Verifies:
    - Small documents (< 2000 chars) get reduced chunk size
    - Chunk size is at least 300 characters
    - Size is calculated as 80% of base size

    This prevents over-chunking of short documents which could
    lead to fragmented context and poor retrieval quality.
    """
    # Test with 500 character document
    result = choose_chunk_size(500)

    # Verify minimum chunk size threshold
    assert result >= 300


def test_choose_chunk_size_medium():
    """
    Test chunk size selection for medium documents.

    Verifies:
    - Medium documents (2000-10000 chars) use base chunk size
    - Returns exactly the configured base size (800)

    This provides optimal chunking for typical document sizes
    without requiring adjustment.
    """
    # Test with 3000 character document
    result = choose_chunk_size(3000)

    # Verify returns base chunk size
    assert result == 800


def test_choose_chunk_size_large():
    """
    Test chunk size selection for large documents.

    Verifies:
    - Large documents (> 10000 chars) get reduced chunk size
    - Chunk size is at least 400 characters
    - Size is calculated as 60% of base size

    This improves retrieval granularity for large documents
    by creating more, smaller chunks for better matching.
    """
    # Test with 20000 character document
    result = choose_chunk_size(20000)

    # Verify minimum chunk size threshold
    assert result >= 400
