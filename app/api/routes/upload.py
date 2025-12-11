"""File upload endpoint with validation and processing."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.schemas.response import APIResponse
from app.api.schemas.upload import UploadResponse
from app.core.exceptions import (
    DocumentProcessingError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from app.domain.uploads.processor import process_upload

router = APIRouter(prefix="/api/upload", tags=["Upload Endpoints"])


@router.post("", response_model=APIResponse[UploadResponse])
async def upload(file: UploadFile = File(...)) -> APIResponse[UploadResponse]:
    """
    Upload and process document file.

    Validates file type and size, saves to disk, extracts text,
    chunks content, generates embeddings, and indexes in database.
    Returns early if file already exists based on content hash.
    """
    try:
        document_id, count, filename = await process_upload(file)
    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UPLOAD_INVALID_FILE_TYPE",
                "message": str(e),
            },
        )
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "UPLOAD_FILE_TOO_LARGE",
                "message": str(e),
            },
        )
    except DocumentProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "UPLOAD_PROCESSING_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "UPLOAD_UNKNOWN_ERROR",
                "message": f"An unexpected error occurred during file upload. [{e}]",
            },
        )

    message = (
        "File uploaded and indexed successfully."
        if count > 0
        else "File was already indexed. Skipped duplicate processing."
    )

    return APIResponse(
        success=True,
        code="UPLOAD_SUCCESS",
        message=message,
        data=UploadResponse(
            filename=filename,
            document_id=document_id,
            chunks_indexed=count,
        ),
    )
