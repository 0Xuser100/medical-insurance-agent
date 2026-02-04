"""
Job Store Service.

Manages job lifecycle for async processing.
MVP: In-memory storage with dict.
Future: Redis/Database implementation.

SOLID: Interface Segregation - JobStoreProtocol defines minimal interface.
SOLID: Open/Closed - Can add Redis/DB implementation without modifying existing code.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol
from uuid import uuid4

from src.models.schemas import (
    ExtractedOCRInput,
    JobStatus,
    PrescriptionValidationResponse,
)


@dataclass
class Job:
    """Represents a processing job."""

    id: str
    status: JobStatus
    filename: str
    file_path: Path
    file_size: int
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    extracted_data: Optional[ExtractedOCRInput] = None
    result: Optional[PrescriptionValidationResponse] = None
    # Event for long polling notification
    _completion_event: asyncio.Event = field(default_factory=asyncio.Event)

    def mark_extracting(self) -> None:
        """Mark job as extracting."""
        self.status = JobStatus.EXTRACTING
        self.started_at = datetime.now()

    def mark_validating(self) -> None:
        """Mark job as validating."""
        self.status = JobStatus.VALIDATING

    def mark_aggregating(self) -> None:
        """Mark job as aggregating (LLM synthesis phase)."""
        self.status = JobStatus.AGGREGATING

    def mark_completed(
        self,
        extracted_data: ExtractedOCRInput,
        result: PrescriptionValidationResponse,
    ) -> None:
        """Mark job as completed with result."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.extracted_data = extracted_data
        self.result = result
        self._completion_event.set()

    def mark_failed(self, error: str) -> None:
        """Mark job as failed with error."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self._completion_event.set()

    async def wait_for_completion(self, timeout: float) -> bool:
        """
        Wait for job completion with timeout.

        Returns True if completed, False if timeout.
        """
        try:
            await asyncio.wait_for(self._completion_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


class JobStoreProtocol(Protocol):
    """
    Protocol for job storage.

    SOLID: Interface Segregation - minimal interface for job storage.
    """

    def create_job(self, filename: str, file_path: Path, file_size: int) -> Job:
        """Create a new job."""
        ...

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        ...

    def update_job(self, job: Job) -> None:
        """Update job state."""
        ...

    def delete_job(self, job_id: str) -> bool:
        """Delete job and associated files."""
        ...


class InMemoryJobStore:
    """
    In-memory job store for MVP.

    Thread-safe dict-based storage.
    For production, replace with Redis or database.
    """

    def __init__(self, uploads_dir: Path):
        """
        Initialize the job store.

        Args:
            uploads_dir: Directory for uploaded files
        """
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self.uploads_dir = uploads_dir

        # Ensure uploads directory exists
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        return f"PAT-{uuid4().hex[:12]}"

    def create_job(self, filename: str, file_path: Path, file_size: int) -> Job:
        """Create a new job."""
        job = Job(
            id=self._generate_job_id(),
            status=JobStatus.UPLOADED,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
        )
        self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def update_job(self, job: Job) -> None:
        """Update job state."""
        self._jobs[job.id] = job

    def delete_job(self, job_id: str) -> bool:
        """Delete job and associated files."""
        job = self._jobs.pop(job_id, None)
        if job:
            # Delete uploaded file
            if job.file_path.exists():
                job.file_path.unlink()
            # Delete extracted JSON if exists
            json_path = job.file_path.with_name(f"{job.id}_extracted.json")
            if json_path.exists():
                json_path.unlink()
            return True
        return False

    def list_jobs(self, status: Optional[JobStatus] = None) -> list[Job]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up jobs older than max_age_hours.

        Returns number of jobs cleaned.
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_delete = [
            job_id
            for job_id, job in self._jobs.items()
            if job.created_at < cutoff
        ]

        for job_id in to_delete:
            self.delete_job(job_id)

        return len(to_delete)
