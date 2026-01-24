"""
File Service.

Handles file upload validation and storage.

SOLID: Single Responsibility - only handles file operations.
"""

from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile


# Allowed MIME types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/tiff",
    "application/pdf",
}

# Allowed extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".tif", ".pdf"}

# Max file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class FileService:
    """
    Handles file upload operations.

    SOLID: Single Responsibility - file handling only.
    """

    def __init__(self, uploads_dir: Path):
        """
        Initialize file service.

        Args:
            uploads_dir: Directory for uploaded files
        """
        self.uploads_dir = uploads_dir
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.

        Raises HTTPException if invalid.
        """
        # Check content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: image/*, application/pdf",
            )

        # Check extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                )

    async def save_file(self, file: UploadFile, job_id: str) -> tuple[Path, int]:
        """
        Save uploaded file to disk.

        Args:
            file: FastAPI UploadFile
            job_id: Job ID to use in filename

        Returns:
            Tuple of (file_path, file_size)

        Raises:
            HTTPException if file too large
        """
        # Generate unique filename using job_id
        ext = Path(file.filename or "upload").suffix.lower()
        unique_name = f"{job_id}{ext}"
        file_path = self.uploads_dir / unique_name

        # Save file with size check
        total_size = 0
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(8192):  # 8KB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    await out_file.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB",
                    )
                await out_file.write(chunk)

        return file_path, total_size

    def delete_file(self, file_path: Path) -> bool:
        """Delete a file if it exists."""
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_extracted_json_path(self, job_id: str) -> Path:
        """Get path for extracted JSON file."""
        return self.uploads_dir / f"{job_id}_extracted.json"
