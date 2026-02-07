"""
Contract tests for GET /result/{job_id} endpoint.

These tests verify the ResultResponse schema matches the OpenAPI contract
defined in specs/002-fix-photo-upload/contracts/get-result-job-id.yaml
"""

import pytest
from datetime import datetime
from src.models.schemas import ResultResponse, JobStatus
from pydantic import ValidationError


def test_result_response_schema_valid():
    """ResultResponse schema should include all required fields."""
    # Test with minimal required fields (processing state)
    response = ResultResponse(
        job_id="PAT-0b1f01e6dc5f",
        status=JobStatus.VALIDATING,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=None,
        error="Processing... Current stage: VALIDATING",
        extracted_data=None,
        result=None,
    )

    assert response.job_id == "PAT-0b1f01e6dc5f"
    assert response.status == JobStatus.VALIDATING
    assert response.created_at is not None
    assert response.started_at is not None
    assert response.completed_at is None
    assert response.error == "Processing... Current stage: VALIDATING"
    assert response.extracted_data is None
    assert response.result is None


def test_result_response_completed_state():
    """ResultResponse for COMPLETED status should allow all fields populated."""
    response = ResultResponse(
        job_id="PAT-abc123def456",
        status=JobStatus.COMPLETED,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        error=None,
        extracted_data=None,  # Would be populated with ExtractedOCRInput in real scenario
        result=None,  # Would be populated with PrescriptionValidationResponse
    )

    assert response.status == JobStatus.COMPLETED
    assert response.completed_at is not None
    assert response.error is None


def test_result_response_failed_state():
    """ResultResponse for FAILED status should include error message."""
    response = ResultResponse(
        job_id="PAT-error123456",
        status=JobStatus.FAILED,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        error="OCR extraction failed: Unable to read image",
        extracted_data=None,
        result=None,
    )

    assert response.status == JobStatus.FAILED
    assert response.error is not None
    assert "OCR extraction failed" in response.error


def test_result_response_requires_job_id():
    """ResultResponse must require job_id field."""
    with pytest.raises(ValidationError) as exc_info:
        ResultResponse(
            status=JobStatus.PROCESSING,
            created_at=datetime.now(),
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("job_id",) for error in errors)


def test_result_response_requires_status():
    """ResultResponse must require status field."""
    with pytest.raises(ValidationError) as exc_info:
        ResultResponse(
            job_id="PAT-test123456",
            created_at=datetime.now(),
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("status",) for error in errors)


def test_result_response_requires_created_at():
    """ResultResponse must require created_at field."""
    with pytest.raises(ValidationError) as exc_info:
        ResultResponse(
            job_id="PAT-test123456",
            status=JobStatus.PROCESSING,
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("created_at",) for error in errors)


def test_result_response_optional_fields_nullable():
    """ResultResponse optional fields (started_at, completed_at, error, extracted_data, result) should be nullable."""
    response = ResultResponse(
        job_id="PAT-upload123456",
        status=JobStatus.UPLOADED,
        created_at=datetime.now(),
        started_at=None,
        completed_at=None,
        error=None,
        extracted_data=None,
        result=None,
    )

    # All optional fields should accept None
    assert response.started_at is None
    assert response.completed_at is None
    assert response.error is None
    assert response.extracted_data is None
    assert response.result is None


def test_result_response_serialization():
    """ResultResponse should serialize to JSON correctly."""
    response = ResultResponse(
        job_id="PAT-serialize123",
        status=JobStatus.PROCESSING,
        created_at=datetime(2026, 2, 7, 18, 37, 55),
        started_at=datetime(2026, 2, 7, 18, 37, 56),
        completed_at=None,
        error="Processing... Current stage: PROCESSING",
        extracted_data=None,
        result=None,
    )

    data = response.model_dump(mode='json')

    assert data["job_id"] == "PAT-serialize123"
    assert data["status"] == "PROCESSING"
    assert data["error"] == "Processing... Current stage: PROCESSING"
    assert data["started_at"] is not None
    assert data["completed_at"] is None
    assert data["extracted_data"] is None
    assert data["result"] is None


def test_result_response_matches_contract_spec():
    """ResultResponse schema should match the OpenAPI contract specification.

    Contract: specs/002-fix-photo-upload/contracts/get-result-job-id.yaml

    Required fields:
    - job_id (string, pattern: ^PAT-[0-9a-f]{12}$)
    - status (enum: JobStatus)
    - created_at (datetime)

    Optional fields (nullable):
    - started_at (datetime)
    - completed_at (datetime)
    - error (string)
    - extracted_data (object)
    - result (object)
    """
    # Test all fields present
    response = ResultResponse(
        job_id="PAT-0b1f01e6dc5f",  # Matches pattern ^PAT-[0-9a-f]{12}$
        status=JobStatus.COMPLETED,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        error=None,
        extracted_data=None,
        result=None,
    )

    # Verify schema structure
    schema = response.model_json_schema()

    # Required fields
    assert "job_id" in schema["required"]
    assert "status" in schema["required"]
    assert "created_at" in schema["required"]

    # Optional fields (should be in properties but not in required)
    assert "started_at" in schema["properties"]
    assert "completed_at" in schema["properties"]
    assert "error" in schema["properties"]
    assert "extracted_data" in schema["properties"]
    assert "result" in schema["properties"]

    assert "started_at" not in schema["required"]
    assert "completed_at" not in schema["required"]
    assert "error" not in schema["required"]
