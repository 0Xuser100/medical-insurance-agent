"""
Core protocols for dependency inversion.

Simplified for LangChain-based validation architecture.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.models.schemas import ExtractedOCRInput, PrescriptionValidationResponse


@runtime_checkable
class ValidationServiceProtocol(Protocol):
    """Interface for validation service."""

    async def validate_prescription(
        self,
        ocr_data: "ExtractedOCRInput",
        job_id: str,
    ) -> "PrescriptionValidationResponse":
        """
        Validate prescription data and return structured response.

        Args:
            ocr_data: Extracted OCR input data
            job_id: Job identifier (used as patient ID)

        Returns:
            Complete prescription validation response
        """
        ...
