"""
FastAPI Application - Medical Insurance Validation API.
"""

import os
from contextlib import asynccontextmanager
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import (
    get_file_service,
    get_job_store,
    get_processing_service,
)
from src.models.schemas import (
    JobStatus,
    ProcessRequest,
    ProcessResponse,
    ResultResponse,
    UploadResponse,
)
from src.services.file_service import FileService
from src.services.job_store import InMemoryJobStore
from src.services.processing_service import ProcessingService

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("Starting Medical Insurance Validation API...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Medical Insurance Validation API",
    description="AI-powered prescription validation with OCR extraction and rule-based checks.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def root():
    """Root endpoint."""
    return {"name": "Medical Insurance Validation API", "version": "0.1.0"}



@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Prescription image or PDF"),
    file_service: FileService = Depends(get_file_service),
    job_store: InMemoryJobStore = Depends(get_job_store),
):
    file_service.validate_file(file)
    job_id = f"PAT-{uuid4().hex[:12]}"
    file_path, file_size = await file_service.save_file(file, job_id)

    job = job_store.create_job(
        filename=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
    )
    job.id = job_id
    job_store._jobs[job_id] = job

    return UploadResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        file_size=job.file_size,
        created_at=job.created_at,
        message="File uploaded. Call POST /process to start.",
    )


@app.post("/process", response_model=ProcessResponse)
async def start_processing(
    request: ProcessRequest,
    processing_service: ProcessingService = Depends(get_processing_service),
    job_store: InMemoryJobStore = Depends(get_job_store),
):
    job = job_store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")

    if job.status in (JobStatus.EXTRACTING, JobStatus.VALIDATING):
        return ProcessResponse(
            job_id=job.id,
            status=job.status,
            message="Already processing.",
        )

    if job.status == JobStatus.COMPLETED:
        return ProcessResponse(
            job_id=job.id,
            status=job.status,
            message=f"Already completed. Check GET /result/{job.id}",
        )

    if job.status == JobStatus.FAILED:
        return ProcessResponse(
            job_id=job.id,
            status=job.status,
            message=f"Failed. Check GET /result/{job.id} for error.",
        )

    started = processing_service.start_processing(request.job_id)
    if not started:
        raise HTTPException(status_code=409, detail="Could not start processing.")

    return ProcessResponse(
        job_id=job.id,
        status=JobStatus.PROCESSING,
        message="Processing started. Poll GET /result/{job_id}",
    )


@app.get("/result/{job_id}", response_model=ResultResponse)
async def get_result(
    job_id: str,
    job_store: InMemoryJobStore = Depends(get_job_store),
):
     
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Still processing - return status message
    if job.status in (
        JobStatus.UPLOADED,
        JobStatus.PROCESSING,
        JobStatus.EXTRACTING,
        JobStatus.VALIDATING,
    ):
        return ResultResponse(
            job_id=job.id,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=None,
            error=f"Processing... Current stage: {job.status.value}",
            extracted_data=None,
            result=None,
        )

    # Completed or Failed - return full result
    return ResultResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error,
        extracted_data=job.extracted_data,
        result=job.result,
    )


@app.delete("/job/{job_id}")
async def delete_job(
    job_id: str,
    job_store: InMemoryJobStore = Depends(get_job_store),
    processing_service: ProcessingService = Depends(get_processing_service),
):
    
    processing_service.cancel_processing(job_id)
    deleted = job_store.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"message": f"Job {job_id} deleted"}


@app.get("/jobs")
async def list_jobs(
    status: JobStatus | None = None,
    job_store: InMemoryJobStore = Depends(get_job_store),
):
    
    jobs = job_store.list_jobs(status=status)
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": j.id,
                "status": j.status,
                "filename": j.filename,
                "created_at": j.created_at,
                "completed_at": j.completed_at,
            }
            for j in jobs
        ],
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("src.api.main:app", host=host, port=port, reload=True)
