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
    REVIEW_NEEDED = "REVIEW_NEEDED"
    REJECTED = "REJECTED"


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
    guardrail: str = Field(..., description="Which guardrail produced this result")


# ============================================================================
# Output Models (JSON Response)
# ============================================================================


class ValidationDetails(BaseModel):
    """Validation details for a line item."""

    clinical_match: bool = Field(default=True, description="Whether item matches diagnosis")
    duration_check: Optional[str] = Field(
        default=None, description="Duration check result"
    )
    reason_en: Optional[str] = Field(
        default="", description="Reason in English"
    )
    reason_ar: Optional[str] = Field(
        default="", description="Reason in Arabic"
    )


class LineItem(BaseModel):
    """A single item in the prescription validation."""

    type: ItemType = Field(default=ItemType.MEDICATION, description="Type of item")
    item_name: str = Field(default="Unknown", description="Name of the item")
    status: ItemStatus = Field(default=ItemStatus.REVIEW_NEEDED, description="Validation status")
    ui_badge: str = Field(default="⚠️ Review Needed", description="Badge text for frontend UI")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level")
    validation_details: ValidationDetails = Field(
        default_factory=ValidationDetails, description="Detailed validation info"
    )


class PatientProfile(BaseModel):
    """Patient profile information."""

    id: str = Field(default="PAT-00000", description="Patient ID")
    name: str = Field(default="Unknown", description="Patient name")
    age: str = Field(default="0", description="Patient age (string for LLM flexibility)")
    gender: str = Field(default="Unknown", description="Patient gender")


class AIValidationEngine(BaseModel):
    """AI validation engine results."""

    overall_status: OverallStatus = Field(default=OverallStatus.REVIEW_NEEDED, description="Overall validation status")
    confidence_score: str = Field(
        default="0.0", description="Confidence/success rate (string for LLM flexibility)"
    )
    medication_count: str = Field(default="0", description="Total medication count (string for LLM flexibility)")
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
    patient_profile: PatientProfile = Field(default_factory=PatientProfile, description="Patient profile")
    ai_validation_engine: AIValidationEngine = Field(
        default_factory=AIValidationEngine, description="Validation results"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "transaction_id": "REQ-2026-5DD7",
            "timestamp": "2026-01-25T10:18:58.813441",
            "patient_profile": {
                "id": "PAT-edce340e42b8",
                "name": "Omar Mohamed Hatem",
                "age": "6",
                "gender": "Male",
            },
            "ai_validation_engine": {
                "overall_status": "APPROVED",
                "confidence_score": "1.0",
                "medication_count": "3",
                "line_items": [
                    {
                        "type": "MEDICATION",
                        "item_name": "Azulast phys N. spray",
                        "status": "APPROVED",
                        "ui_badge": "✓ Approved",
                        "risk_level": "LOW",
                        "validation_details": {
                            "clinical_match": True,
                            "duration_check": "OK",
                            "reason_en": "Clinically appropriate for diagnosis",
                            "reason_ar": "مناسب سريرياً للتشخيص",
                        },
                    },
                ],
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
    AGGREGATING = "AGGREGATING"
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
    started_at: Optional[datetime] = Field(
        default=None, description="Processing start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Processing completion timestamp"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed or processing status")
    extracted_data: Optional[ExtractedOCRInput] = Field(
        default=None, description="Extracted OCR data from image/PDF"
    )
    result: Optional[PrescriptionValidationResponse] = Field(
        default=None, description="Validation result if completed"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "job_id": "PAT-edce340e42b8",
            "status": "COMPLETED",
            "created_at": "2026-01-25T10:15:26.166367",
            "started_at": "2026-01-25T10:15:50.474445",
            "completed_at": "2026-01-25T10:18:58.813960",
            "error": None,
            "extracted_data": {
                "doctor_information": {
                    "name": "Dr. Wael Hatem El Taei",
                    "specialization": "Consultant Pediatrician and Neonatologist",
                },
                "patient_information": {
                    "name": "Omar Mohamed Hatem",
                    "age": "6.5 years",
                    "weight": "20.4 kg",
                },
                "medications": [
                    {"name": "Azulast phys N. spray", "dosage": "One puff in each nostril twice daily", "duration": "One month"},
                    {"name": "Lelipel syrup", "dosage": "5 ml in the evening", "duration": "One month"},
                ],
            },
            "result": {
                "transaction_id": "REQ-2026-5DD7",
                "timestamp": "2026-01-25T10:18:58.813441",
                "patient_profile": {
                    "id": "PAT-edce340e42b8",
                    "name": "Omar Mohamed Hatem",
                    "age": "6",
                    "gender": "Male",
                },
                "ai_validation_engine": {
                    "overall_status": "APPROVED",
                    "confidence_score": "1.0",
                    "medication_count": "3",
                    "line_items": [
                        {
                            "type": "MEDICATION",
                            "item_name": "Azulast phys N. spray",
                            "status": "APPROVED",
                            "ui_badge": "✓ Approved",
                            "risk_level": "LOW",
                            "validation_details": {
                                "clinical_match": True,
                                "duration_check": "OK",
                                "reason_en": "Clinically appropriate for diagnosis",
                                "reason_ar": "مناسب سريرياً للتشخيص",
                            },
                        },
                    ],
                },
            }
        }
    }}
