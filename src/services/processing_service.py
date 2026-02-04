"""
Processing Service.

Handles background processing of validation jobs.

SOLID: Single Responsibility - orchestrates processing only.
SOLID: Dependency Inversion - depends on injected services.
"""

import asyncio
from pathlib import Path

from loguru import logger

from src.models.schemas import JobStatus
from src.services.extraction_service import ExtractionService
from src.services.job_store import InMemoryJobStore, Job
from src.services.langchain_validation_service import LangChainValidationService


class ProcessingService:
    """
    Orchestrates background job processing.

    Uses LangChain + Gemini for unified validation.
    """

    def __init__(
        self,
        job_store: InMemoryJobStore,
        validation_service: LangChainValidationService,
        extraction_service: ExtractionService,
        uploads_dir: Path,
    ):
        """
        Initialize processing service.

        Args:
            job_store: Job storage service
            validation_service: LangChain validation service
            extraction_service: Gemini extraction service
            uploads_dir: Directory for uploads and extracted JSONs
        """
        self.job_store = job_store
        self.validation_service = validation_service
        self.extraction_service = extraction_service
        self.uploads_dir = uploads_dir
        self._running_tasks: dict[str, asyncio.Task] = {}

    def _get_extracted_json_path(self, job_id: str) -> Path:
        """Get path for extracted JSON file."""
        return self.uploads_dir / f"{job_id}_extracted.json"

    async def _process_job(self, job: Job) -> None:
        """Process a single job in background."""
        logger.info(f"ProcessingService: Starting job {job.id}")
        try:
            # Phase 1: Extraction (Gemini OCR)
            logger.info(f"Job {job.id}: Phase 1 - Extraction starting")
            job.mark_extracting()
            self.job_store.update_job(job)

            save_path = self._get_extracted_json_path(job.id)
            extracted_data = await self.extraction_service.extract_from_file(
                file_path=job.file_path,
                save_path=save_path,
            )
            medications = extracted_data.get("medications", [])
            logger.info(f"Job {job.id}: Extraction complete - {len(medications)} medications found")

            # Phase 2: Validation (LangChain + Gemini)
            logger.info(f"Job {job.id}: Phase 2 - Validation starting")
            job.mark_validating()
            job.extracted_data = extracted_data
            self.job_store.update_job(job)

            # Single LangChain call replaces multi-agent system
            result = await self.validation_service.validate_prescription(extracted_data, job_id=job.id)
            logger.info(f"Job {job.id}: Validation complete - Status: {result.ai_validation_engine.overall_status.value}")

            job.mark_completed(extracted_data=extracted_data, result=result)
            self.job_store.update_job(job)
            logger.info(f"Job {job.id}: Processing completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id}: Processing failed - {str(e)}")
            job.mark_failed(str(e))
            self.job_store.update_job(job)

        finally:
            self._running_tasks.pop(job.id, None)

    def start_processing(self, job_id: str) -> bool:
        """Start processing a job in background."""
        job = self.job_store.get_job(job_id)
        if not job:
            logger.warning(f"ProcessingService: Job {job_id} not found")
            return False

        if job.status != JobStatus.UPLOADED:
            logger.warning(f"ProcessingService: Job {job_id} not in UPLOADED status (current: {job.status})")
            return False

        if job_id in self._running_tasks:
            logger.warning(f"ProcessingService: Job {job_id} already running")
            return False

        logger.info(f"ProcessingService: Starting background task for job {job_id}")
        task = asyncio.create_task(self._process_job(job))
        self._running_tasks[job_id] = task

        return True

    def cancel_processing(self, job_id: str) -> bool:
        """Cancel a running job."""
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            logger.info(f"ProcessingService: Cancelling job {job_id}")
            task.cancel()
            return True
        return False

    def is_processing(self, job_id: str) -> bool:
        """Check if a job is currently processing."""
        task = self._running_tasks.get(job_id)
        return task is not None and not task.done()
