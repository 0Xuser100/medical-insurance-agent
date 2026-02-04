"""
Dependency Injection for FastAPI.

Simplified for LangChain-based validation architecture.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from src.services.extraction_service import ExtractionService
from src.services.file_service import FileService
from src.services.job_store import InMemoryJobStore
from src.services.langchain_validation_service import LangChainValidationService
from src.services.processing_service import ProcessingService

load_dotenv()


@lru_cache
def get_mappings_path() -> Path:
    """Get path to diagnosis mappings file."""
    return Path(__file__).parent.parent / "data" / "diagnosis_mappings.json"


@lru_cache
def get_medication_limit() -> int:
    """Get medication limit from environment or default."""
    return int(os.getenv("MEDICATION_LIMIT", "5"))


@lru_cache
def get_min_duration_days() -> int:
    """Get minimum duration days from environment or default."""
    return int(os.getenv("MIN_DURATION_DAYS", "14"))


@lru_cache
def get_validation_service() -> LangChainValidationService:
    """Get or create the LangChain validation service."""
    return LangChainValidationService(
        mappings_path=get_mappings_path(),
        medication_limit=get_medication_limit(),
        min_duration_days=get_min_duration_days(),
    )


@lru_cache
def get_uploads_dir() -> Path:
    """Get uploads directory path."""
    uploads_dir = Path(__file__).parent.parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


@lru_cache
def get_job_store() -> InMemoryJobStore:
    """Get or create the job store."""
    return InMemoryJobStore(uploads_dir=get_uploads_dir())


@lru_cache
def get_file_service() -> FileService:
    """Get or create the file service."""
    return FileService(uploads_dir=get_uploads_dir())


@lru_cache
def get_extraction_service() -> ExtractionService:
    """Get or create the extraction service."""
    return ExtractionService()


@lru_cache
def get_processing_service() -> ProcessingService:
    """Get or create the processing service."""
    return ProcessingService(
        job_store=get_job_store(),
        validation_service=get_validation_service(),
        extraction_service=get_extraction_service(),
        uploads_dir=get_uploads_dir(),
    )
