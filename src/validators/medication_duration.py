"""
Medication Duration Validator - Guardrail 3.

Ensures minimum 2 weeks between same medication prescriptions.

SOLID: Single Responsibility - only handles duration check.

Note: Without medication_history from external systems, this validator
always approves medications. Future integration with patient history
systems would enable full duration checking.
"""

from loguru import logger

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

    Note: Without medication_history (not extracted from prescriptions),
    this validator approves all medications by default.
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

    def _extract_medication_name(self, medication: str | dict) -> str:
        """Extract medication name from string or dict format."""
        if isinstance(medication, dict):
            return medication.get("name", str(medication))
        return medication

    async def validate(self, data: ExtractedOCRInput) -> list[ValidationResult]:
        """
        Check if any medication was dispensed too recently.

        Note: Without medication_history available, all medications pass by default.

        Args:
            data: Extracted OCR input data (raw dict from Gemini)

        Returns:
            List of validation results for medications
        """
        medications = data.get("medications", [])
        logger.info(f"MedicationDurationValidator: Validating {len(medications)} medications")
        results: list[ValidationResult] = []

        # No medication history available - all medications pass by default
        for medication in medications:
            med_name = self._extract_medication_name(medication)
            logger.debug(f"Medication '{med_name}' APPROVED (no prior history available)")
            results.append(
                ValidationResult(
                    item_name=med_name,
                    item_type=ItemType.MEDICATION,
                    status=ItemStatus.APPROVED,
                    risk_level=RiskLevel.LOW,
                    clinical_match=True,
                    duration_check="Passed (No prior history available)",
                    guardrail=self.name,
                )
            )

        logger.info(f"MedicationDurationValidator: Completed. {len(results)} results")
        return results
