"""
Medication Limit Validator - Guardrail 2.

Flags prescriptions with more than 5 medications for doctor review.

SOLID: Single Responsibility - only handles medication count check.
"""

from src.models.schemas import (
    ExtractedOCRInput,
    ItemStatus,
    ItemType,
    RiskLevel,
    ValidationResult,
)
from src.validators.base import BaseValidator


class MedicationLimitValidator(BaseValidator):
    """
    Guardrail 2: Medication Limit Check.

    Flags prescriptions with too many medications for doctor review.
    Default limit is 5 medications.
    """

    def __init__(self, limit: int = 5):
        """
        Initialize the medication limit validator.

        Args:
            limit: Maximum number of medications before flagging (default: 5)
        """
        self.limit = limit

    @property
    def name(self) -> str:
        return "medication_limit"

    async def validate(self, data: ExtractedOCRInput) -> list[ValidationResult]:
        """
        Check if the prescription exceeds the medication limit.

        Args:
            data: Extracted OCR input data

        Returns:
            List with a single result indicating limit status
        """
        medication_count = len(data.medications)

        if medication_count <= self.limit:
            # Within limit - no action needed
            return []

        # Exceeds limit - flag for doctor review
        return [
            ValidationResult(
                item_name=f"Prescription ({medication_count} medications)",
                item_type=ItemType.MEDICATION,
                status=ItemStatus.PENDING_REVIEW,
                risk_level=RiskLevel.MEDIUM,
                clinical_match=True,
                reason_en=f"Prescription contains {medication_count} medications. "
                f"Exceeds limit of {self.limit}. Doctor review required for polypharmacy risk.",
                reason_ar=f"الوصفة تحتوي على {medication_count} أدوية. "
                f"تتجاوز الحد المسموح ({self.limit}). مطلوب مراجعة الطبيب.",
                guardrail=self.name,
            )
        ]
