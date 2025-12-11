"""Custom exception classes for RAG application."""


class RAGException(Exception):
    """Base exception for all RAG-related errors."""

    pass


class InvalidFileTypeError(RAGException):
    """Raised when uploaded file type is not supported."""

    pass


class FileTooLargeError(RAGException):
    """Raised when uploaded file exceeds maximum size limit."""

    pass


class DocumentProcessingError(RAGException):
    """Raised when document processing fails."""

    pass


class EmbeddingError(RAGException):
    """Raised when embedding generation fails."""

    pass


class DatabaseError(RAGException):
    """Raised when database operations fail."""

    pass
