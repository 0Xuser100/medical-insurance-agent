"""
Pydantic models for the Medical Insurance Validation Agent.

Based on the JSON schema defined in README.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Type Aliases
# ============================================================================

# Flexible type for Gemini OCR output - accepts any dict structure
ExtractedOCRInput = dict[str, Any]


# ============================================================================
# Enums
# ============================================================================


class ItemType(str, Enum):
    """Type of prescription item."""

    MEDICATION = "MEDICATION"
    LAB_ANALYSIS = "LAB_ANALYSIS"
    RADIOLOGY = "RADIOLOGY"
    PROCEDURE = "PROCEDURE"


class ItemStatus(str, Enum):
    """Validation status of an item."""

    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    PENDING_REVIEW = "PENDING_REVIEW"


class RiskLevel(str, Enum):
    """Risk level of a flagged item."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OverallStatus(str, Enum):
    """Overall prescription validation status."""

    APPROVED = "APPROVED"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    REJECTED = "REJECTED"


# ============================================================================
# Input Models
# ============================================================================

# NOTE: ExtractedOCRInput is defined above as a type alias (dict[str, Any])
# This allows Gemini to return any structure without validation constraints.


# ============================================================================
# Intermediate Models
# ============================================================================


class ValidationResult(BaseModel):
    """
    Result from a single validation check.

    Used internally to pass results between validators and report builder.
    """

    item_name: str = Field(..., description="Name of the validated item")
    item_type: ItemType = Field(..., description="Type of item")
    status: ItemStatus = Field(..., description="Validation status")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level")
    clinical_match: bool = Field(default=True, description="Clinical match passed")
    duration_check: Optional[str] = Field(
        default=None, description="Duration check result"
    )
    reason_en: Optional[str] = Field(
        default=None, description="Reason in English"
    )
    reason_ar: Optional[str] = Field(
        default=None, description="Reason in Arabic"
    )
    linked_history_id: Optional[str] = Field(
        default=None, description="Linked history claim ID"
    )
    guardrail: str = Field(..., description="Which guardrail produced this result")


# ============================================================================
# Output Models (JSON Response)
# ============================================================================


class ValidationDetails(BaseModel):
    """Validation details for a line item."""

    clinical_match: bool = Field(..., description="Whether item matches diagnosis")
    duration_check: Optional[str] = Field(
        default=None, description="Duration check result"
    )
    reason_en: Optional[str] = Field(
        default=None, description="Reason in English"
    )
    reason_ar: Optional[str] = Field(
        default=None, description="Reason in Arabic"
    )
    linked_history_id: Optional[str] = Field(
        default=None, description="Linked previous claim ID for audit"
    )


class LineItem(BaseModel):
    """A single item in the prescription validation."""

    type: ItemType = Field(..., description="Type of item")
    item_name: str = Field(..., description="Name of the item")
    status: ItemStatus = Field(..., description="Validation status")
    ui_badge: str = Field(..., description="Badge text for frontend UI")
    risk_level: RiskLevel = Field(..., description="Risk level")
    validation_details: ValidationDetails = Field(
        ..., description="Detailed validation info"
    )


class PatientProfile(BaseModel):
    """Patient profile information."""

    id: str = Field(..., description="Patient ID")
    name: str = Field(..., description="Patient name")
    age: int = Field(..., description="Patient age")
    gender: str = Field(..., description="Patient gender")
    insurance_tier: str = Field(default="Unknown", description="Insurance tier")
    history_summary: str = Field(
        default="", description="Summary of patient medical history"
    )


class ExtractedContext(BaseModel):
    """Context extracted from the prescription."""

    primary_diagnosis: str = Field(..., description="Primary diagnosis")
    icd_code: str = Field(..., description="ICD-10 code")
    provider_id: str = Field(..., description="Provider ID")


class AIValidationEngine(BaseModel):
    """AI validation engine results."""

    overall_status: OverallStatus = Field(..., description="Overall validation status")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence/success rate"
    )
    summary_message: str = Field(..., description="Summary message for UI")
    medication_count: int = Field(default=0, description="Total medication count")
    line_items: list[LineItem] = Field(
        default_factory=list, description="Validated line items"
    )


class PrescriptionValidationResponse(BaseModel):
    """
    Complete prescription validation response.

    This is the final JSON output sent to the frontend.
    """

    transaction_id: str = Field(
        default_factory=lambda: f"REQ-{datetime.now().strftime('%Y')}-{uuid4().hex[:4].upper()}",
        description="Unique transaction ID",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of validation"
    )
    patient_profile: PatientProfile = Field(..., description="Patient profile")
    extracted_context: ExtractedContext = Field(..., description="Extracted context")
    ai_validation_engine: AIValidationEngine = Field(
        ..., description="Validation results"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "transaction_id": "REQ-2024-8859",
            "timestamp": "2024-05-21T10:30:00Z",
            "patient_profile": {
                "id": "PAT-10023",
                "name": "Ahmed Hassan",
                "age": 45,
                "gender": "Male",
                "insurance_tier": "Gold",
                "history_summary": "",
            },
            "extracted_context": {
                "primary_diagnosis": "Acute Bronchitis",
                "icd_code": "J20.9",
                "provider_id": "DR-5501",
            },
            "ai_validation_engine": {
                "overall_status": "REVIEW_NEEDED",
                "confidence_score": 0.75,
                "summary_message": "Request partially approved.",
                "medication_count": 3,
                "line_items": [],
            },
        }
    }}


# ============================================================================
# Job/Async Processing Models
# ============================================================================


class JobStatus(str, Enum):
    """Status of a processing job."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UploadResponse(BaseModel):
    """Response from file upload endpoint."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.UPLOADED, description="Job status")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Upload timestamp"
    )
    message: str = Field(
        default="File uploaded successfully", description="Status message"
    )


class ProcessRequest(BaseModel):
    """Request to start processing a job."""

    job_id: str = Field(..., description="Job ID to process")


class ProcessResponse(BaseModel):
    """Response from process start endpoint."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class ResultResponse(BaseModel):
    """Response from result polling endpoint."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime = Field(
        default=None, description="Processing start timestamp"
    )
    completed_at: datetime = Field(
        default=None, description="Processing completion timestamp"
    )
    signal: Optional[str] = Field(default=None, description="Signal if failed")
    extracted_data: Optional[ExtractedOCRInput] = Field(
        default=None, description="Extracted OCR data from image/PDF"
    )
    result: PrescriptionValidationResponse = Field(
        default=None, description="Validation result if completed"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "job_id": "PAT-1234567890AB",
            "status": "COMPLETED",
            "created_at": "2026-01-24T15:54:29.873Z",
            "started_at": "2026-01-24T15:54:29.873Z",
            "completed_at": "2026-01-24T15:54:29.873Z",
            "signal": None,
            "extracted_data": {
                "medications": [
                    {"name": "Azulast phys N. spray", "dosage": "One puff...", "duration": "One month"}
                ]
            },
            "result": {
                "transaction_id": "REQ-2024-8859",
                "timestamp": "2024-05-21T10:30:00Z",
                "patient_profile": {
                    "id": "PAT-10023",
                    "name": "Ahmed Hassan",
                    "age": 45,
                    "gender": "Male",
                    "insurance_tier": "Gold",
                    "history_summary": "",
                },
                "extracted_context": {
                    "primary_diagnosis": "Acute Bronchitis",
                    "icd_code": "J20.9",
                    "provider_id": "DR-5501",
                },
                "ai_validation_engine": {
                    "overall_status": "REVIEW_NEEDED",
                    "confidence_score": 0.75,
                    "summary_message": "Request partially approved.",
                    "medication_count": 3,
                    "line_items": [],
                },
            }
        }
    }}
