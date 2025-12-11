"""Unit tests for content-based file hashing."""

from app.domain.documents.hashing import compute_file_hash


def test_compute_file_hash(tmp_path):
    """
    Test SHA-256 hash generation for file contents.

    Verifies:
    - Hash is generated successfully
    - Hash is returned as string
    - Hash length is 64 characters (SHA-256 hex format)

    The hash is used for duplicate detection during file upload.
    Files with identical content will produce the same hash,
    allowing the system to skip redundant indexing.

    Args:
        tmp_path: Pytest fixture providing temporary directory
    """
    # Create test file with known content
    file = tmp_path / "test.txt"
    file.write_text("hello test")

    # Compute SHA-256 hash of file contents
    result = compute_file_hash(str(file))

    # Verify hash format
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 produces 64 hex characters
