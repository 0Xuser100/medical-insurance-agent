"""
Dependency Injection for FastAPI.

SOLID: Dependency Inversion
- Provides factory functions for all dependencies
- Easily extendable to add new validators
- Configurable via environment variables
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from src.agents.validation_crew import ValidationCrew
from src.core.protocols import ValidatorProtocol
from src.services.extraction_service import ExtractionService
from src.services.file_service import FileService
from src.services.job_store import InMemoryJobStore
from src.services.processing_service import ProcessingService
from src.services.report_builder import ReportBuilder
from src.services.validation_service import ValidationService
from src.validators.clinical_match import ClinicalMatchValidator
from src.validators.medication_duration import MedicationDurationValidator
from src.validators.medication_limit import MedicationLimitValidator

# Load environment variables
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
def get_validators() -> list[ValidatorProtocol]:
    """
    Factory for validators.

    SOLID: Open/Closed Principle
    - Add new validators here without modifying existing code
    """
    return [
        ClinicalMatchValidator(mappings_path=get_mappings_path()),
        MedicationLimitValidator(limit=get_medication_limit()),
        MedicationDurationValidator(min_days=get_min_duration_days()),
    ]


@lru_cache
def get_validation_service() -> ValidationService:
    """Get or create the validation service."""
    return ValidationService(validators=get_validators())


@lru_cache
def get_report_builder() -> ReportBuilder:
    """Get or create the report builder."""
    return ReportBuilder()


@lru_cache
def get_validation_crew() -> ValidationCrew:
    """
    Get or create the multi-agent validation crew.

    SOLID: Dependency Inversion
    - ValidationCrew depends on ReportBuilder for final output
    - Three specialized agents handle validation independently
    - Pydantic validation happens only at report building stage
    """
    return ValidationCrew(
        report_builder=get_report_builder(),
    )


# ============================================================================
# Async Processing Dependencies
# ============================================================================


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
        validation_crew=get_validation_crew(),
        extraction_service=get_extraction_service(),
        uploads_dir=get_uploads_dir(),
    )
