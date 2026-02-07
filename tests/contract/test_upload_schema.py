"""Contract tests for UploadResponse schema alignment.

Verifies that the backend UploadResponse Pydantic model serializes
with the exact fields the frontend expects.
"""

import json
from datetime import datetime

from src.models.schemas import JobStatus, UploadResponse


EXPECTED_FIELDS = {"job_id", "status", "filename", "file_size", "created_at", "message"}


def _make_upload_response() -> UploadResponse:
    return UploadResponse(
        job_id="550e8400-e29b-41d4-a716-446655440000",
        status=JobStatus.UPLOADED,
        filename="prescription_scan.jpg",
        file_size=245768,
        created_at=datetime(2026, 2, 7, 14, 23, 45),
        message="File uploaded successfully",
    )


def test_upload_response_has_all_required_fields():
    """UploadResponse JSON must contain exactly the fields the frontend expects."""
    response = _make_upload_response()
    data = json.loads(response.model_dump_json())
    assert set(data.keys()) == EXPECTED_FIELDS


def test_upload_response_field_types():
    """Verify serialized field types match frontend Zod expectations."""
    response = _make_upload_response()
    data = json.loads(response.model_dump_json())

    assert isinstance(data["job_id"], str)
    assert isinstance(data["status"], str)
    assert isinstance(data["filename"], str)
    assert isinstance(data["file_size"], int)
    assert isinstance(data["created_at"], str)
    assert isinstance(data["message"], str)


def test_upload_response_status_enum():
    """Status value must be a valid JobStatus enum string."""
    response = _make_upload_response()
    data = json.loads(response.model_dump_json())
    valid_statuses = {s.value for s in JobStatus}
    assert data["status"] in valid_statuses


def test_upload_response_file_size_positive():
    """file_size must be a positive integer."""
    response = _make_upload_response()
    data = json.loads(response.model_dump_json())
    assert data["file_size"] > 0


def test_upload_response_does_not_contain_job_result_fields():
    """UploadResponse must NOT contain started_at, completed_at, error (those belong to ResultResponse)."""
    response = _make_upload_response()
    data = json.loads(response.model_dump_json())
    assert "started_at" not in data
    assert "completed_at" not in data
    assert "error" not in data
