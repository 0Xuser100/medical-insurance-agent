"""
Clinical Match Validator - Guardrail 1.

Validates that medications align with the diagnosis.

SOLID: Single Responsibility - only handles clinical matching.
"""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from src.models.schemas import (
    ExtractedOCRInput,
    ItemStatus,
    ItemType,
    RiskLevel,
    ValidationResult,
)
from src.validators.base import BaseValidator


class ClinicalMatchValidator(BaseValidator):
    """
    Guardrail 1: Clinical Match Check.

    Validates that each medication and lab is appropriate for the diagnosis.
    Uses diagnosis_mappings.json as the data source.
    """

    def __init__(self, mappings_path: str | Path | None = None):
        """
        Initialize the clinical match validator.

        Args:
            mappings_path: Path to diagnosis_mappings.json
        """
        if mappings_path is None:
            # Default path relative to project root
            mappings_path = Path(__file__).parent.parent / "data" / "diagnosis_mappings.json"

        self.mappings_path = Path(mappings_path)
        self._mappings: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "clinical_match"

    @property
    def mappings(self) -> dict[str, Any]:
        """Lazy load mappings from JSON file."""
        if self._mappings is None:
            self._mappings = self._load_mappings()
        return self._mappings

    def _load_mappings(self) -> dict[str, Any]:
        """Load diagnosis mappings from JSON file."""
        if not self.mappings_path.exists():
            return {}

        with open(self.mappings_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize_name(self, name: str) -> str:
        """Normalize medication/lab name for comparison."""
        # Remove dosage info (e.g., "Azithromycin 500mg" -> "azithromycin")
        parts = name.lower().split()
        if parts:
            # Take first word as the medication name
            return parts[0]
        return name.lower()

    def _is_valid_for_diagnosis(
        self, item_name: str, icd_code: str, item_type: ItemType
    ) -> tuple[bool, str | None, str | None]:
        """
        Check if an item is valid for the given diagnosis.

        Returns:
            Tuple of (is_valid, reason_en, reason_ar)
        """
        diagnosis_data = self.mappings.get(icd_code)

        if diagnosis_data is None:
            # Unknown diagnosis - allow by default with warning
            return True, None, None

        normalized_name = self._normalize_name(item_name)

        if item_type == ItemType.MEDICATION:
            valid_items = [
                self._normalize_name(m)
                for m in diagnosis_data.get("valid_medications", [])
            ]
        else:
            valid_items = [
                self._normalize_name(l)
                for l in diagnosis_data.get("valid_labs", [])
            ]

        if normalized_name in valid_items:
            return True, None, None

        diagnosis_name = diagnosis_data.get("name", icd_code)
        diagnosis_name_ar = diagnosis_data.get("name_ar", diagnosis_name)

        reason_en = f"Not indicated for {diagnosis_name} diagnosis."
        reason_ar = f"الدواء غير مناسب لتشخيص {diagnosis_name_ar}"

        return False, reason_en, reason_ar

    def _extract_medication_name(self, medication: str | dict) -> str:
        """Extract medication name from string or dict format."""
        if isinstance(medication, dict):
            return medication.get("name", str(medication))
        return medication

    async def validate(self, data: ExtractedOCRInput) -> list[ValidationResult]:
        """
        Validate all medications against the diagnosis.

        Args:
            data: Extracted OCR input data (raw dict from Gemini)

        Returns:
            List of validation results for each medication
        """
        # Extract fields with fallbacks
        medications = data.get("medications", [])
        icd_code = data.get("icd_code", "")

        logger.info(f"ClinicalMatchValidator: Validating {len(medications)} medications for ICD: {icd_code}")
        results: list[ValidationResult] = []

        # Validate medications only
        for medication in medications:
            med_name = self._extract_medication_name(medication)
            is_valid, reason_en, reason_ar = self._is_valid_for_diagnosis(
                med_name, icd_code, ItemType.MEDICATION
            )

            if is_valid:
                logger.debug(f"Medication '{med_name}' APPROVED for {icd_code}")
                results.append(
                    ValidationResult(
                        item_name=med_name,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.APPROVED,
                        risk_level=RiskLevel.LOW,
                        clinical_match=True,
                        guardrail=self.name,
                    )
                )
            else:
                logger.warning(f"Medication '{med_name}' FLAGGED: {reason_en}")
                results.append(
                    ValidationResult(
                        item_name=med_name,
                        item_type=ItemType.MEDICATION,
                        status=ItemStatus.FLAGGED,
                        risk_level=RiskLevel.HIGH,
                        clinical_match=False,
                        reason_en=reason_en,
                        reason_ar=reason_ar,
                        guardrail=self.name,
                    )
                )

        logger.info(f"ClinicalMatchValidator: Completed. {len(results)} results")
        return results
