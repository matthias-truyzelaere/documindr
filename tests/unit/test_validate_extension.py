"""Unit tests for file extension validation."""

from app.domain.uploads.processor import validate_extension


def test_validate_extension_allowed():
    """
    Test validation accepts allowed file extensions.

    Verifies:
    - PDF files (.pdf) are accepted
    - Word documents (.docx) are accepted
    - Text files (.txt) are accepted

    These file types are supported by the document loader
    and can be processed for text extraction and indexing.
    """
    # Test allowed extensions
    assert validate_extension("file.pdf") is True
    assert validate_extension("notes.docx") is True
    assert validate_extension("text.txt") is True


def test_validate_extension_disallowed():
    """
    Test validation rejects disallowed file extensions.

    Verifies:
    - Image files (.jpg) are rejected
    - Python scripts (.py) are rejected

    These file types are not supported for text extraction
    and indexing, so they are rejected during upload validation.

    Rejecting unsupported file types early prevents:
    - Wasted processing on files that cannot be loaded
    - Confusing error messages later in the pipeline
    - Storage of files that cannot be indexed
    """
    # Test disallowed extensions
    assert validate_extension("image.jpg") is False
    assert validate_extension("script.py") is False
