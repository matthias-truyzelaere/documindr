"""Content-based file hashing for duplicate detection."""

import hashlib


def compute_file_hash(path: str) -> str:
    """Generate SHA-256 hash of file contents for duplicate detection."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()
