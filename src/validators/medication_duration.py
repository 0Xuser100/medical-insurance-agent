"""
Medication Duration Validator - Guardrail 3.

Ensures minimum 2 weeks between same medication prescriptions.

SOLID: Single Responsibility - only handles duration check.
"""

from src.models.schemas import (
    ExtractedOCRInput,
    ItemStatus,
    ItemType,
    RiskLevel,
    ValidationResult,
)
from src.validators.base import BaseValidator


class MedicationDurationValidator(BaseValidator):
    """
    Guardrail 3: Medication Duration Check.

    Ensures minimum time between same medication prescriptions.
    Default minimum is 14 days (2 weeks).
    """

    def __init__(self, min_days: int = 14):
        """
        Initialize the medication duration validator.

        Args:
            min_days: Minimum days between same medication (default: 14)
        """
        self.min_days = min_days

    @property
    def name(self) -> str:
        return "medication_duration"

    def _normalize_name(self, name: str) -> str:
        """Normalize medication name for comparison."""
        # Remove dosage info (e.g., "Panadol Extra" -> "panadol extra")
        return name.lower().strip()

    async def validate(self, data: ExtractedOCRInput) -> list[ValidationResult]:
        """
        Check if any medication was dispensed too recently.

        Args:
            data: Extracted OCR input data

        Returns:
            List of validation results for medications with duration issues
        """
        results: list[ValidationResult] = []

        if not data.medication_history:
            # No history provided - all medications pass by default
            for medication in data.medications:
                results.append(
                    ValidationResult(
                        item_name=medication,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.APPROVED,
                        risk_level=RiskLevel.LOW,
                        clinical_match=True,
                        duration_check="Passed (No prior history)",
                        guardrail=self.name,
                    )
                )
            return results

        # Check each medication against history
        for medication in data.medications:
            normalized_name = self._normalize_name(medication)

            # Find matching history entry
            days_since_last = None
            for hist_med, days in data.medication_history.items():
                if self._normalize_name(hist_med) in normalized_name or normalized_name in self._normalize_name(hist_med):
                    days_since_last = days
                    break

            if days_since_last is None:
                # No history for this medication
                results.append(
                    ValidationResult(
                        item_name=medication,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.APPROVED,
                        risk_level=RiskLevel.LOW,
                        clinical_match=True,
                        duration_check="Passed (No prior dispensing)",
                        guardrail=self.name,
                    )
                )
            elif days_since_last >= self.min_days:
                # Sufficient time has passed
                results.append(
                    ValidationResult(
                        item_name=medication,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.APPROVED,
                        risk_level=RiskLevel.LOW,
                        clinical_match=True,
                        duration_check=f"Passed (Last dispensed: {days_since_last} days ago)",
                        guardrail=self.name,
                    )
                )
            else:
                # Too soon to refill
                results.append(
                    ValidationResult(
                        item_name=medication,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.FLAGGED,
                        risk_level=RiskLevel.MEDIUM,
                        clinical_match=True,
                        duration_check="FAILED",
                        reason_en=f"Patient received this medication {days_since_last} days ago. "
                        f"Minimum {self.min_days} days required.",
                        reason_ar=f"المريض صرف هذا الدواء منذ {days_since_last} أيام. "
                        f"يجب الانتظار {self.min_days} يوم على الأقل.",
                        linked_history_id=f"HIST-{medication[:3].upper()}-{days_since_last}",
                        guardrail=self.name,
                    )
                )

        return results
