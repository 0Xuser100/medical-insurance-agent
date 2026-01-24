"""
Tests for validators.
"""

import pytest

from src.models.schemas import ExtractedOCRInput, ItemStatus, ItemType
from src.validators.clinical_match import ClinicalMatchValidator
from src.validators.medication_duration import MedicationDurationValidator
from src.validators.medication_limit import MedicationLimitValidator


@pytest.fixture
def sample_input() -> ExtractedOCRInput:
    """Create sample input for testing (raw dict format)."""
    return {
        "patient_name": "Ahmed Hassan",
        "age": 45,
        "gender": "Male",
        "diagnosis": "Acute Bronchitis",
        "icd_code": "J20.9",
        "provider_id": "DR-5501",
        "medications": ["Azithromycin 500mg", "Propranolol", "Panadol Extra"],
    }


class TestClinicalMatchValidator:
    """Tests for ClinicalMatchValidator."""

    @pytest.mark.asyncio
    async def test_valid_medication_approved(self, sample_input: ExtractedOCRInput):
        """Test that valid medications are approved."""
        validator = ClinicalMatchValidator()
        results = await validator.validate(sample_input)

        # Azithromycin should be approved for Acute Bronchitis
        azithromycin_result = next(
            r for r in results if "Azithromycin" in r.item_name
        )
        assert azithromycin_result.status == ItemStatus.APPROVED
        assert azithromycin_result.clinical_match is True

    @pytest.mark.asyncio
    async def test_invalid_medication_flagged(self, sample_input: ExtractedOCRInput):
        """Test that invalid medications are flagged."""
        validator = ClinicalMatchValidator()
        results = await validator.validate(sample_input)

        # Propranolol should be flagged for Acute Bronchitis
        propranolol_result = next(
            r for r in results if "Propranolol" in r.item_name
        )
        assert propranolol_result.status == ItemStatus.FLAGGED
        assert propranolol_result.clinical_match is False
        assert propranolol_result.reason_en is not None

    @pytest.mark.asyncio
    async def test_only_medications_validated(self, sample_input: ExtractedOCRInput):
        """Test that only medications are validated (no labs)."""
        validator = ClinicalMatchValidator()
        results = await validator.validate(sample_input)

        # Should only have results for medications
        assert len(results) == 3  # 3 medications
        for result in results:
            assert result.item_type == ItemType.MEDICATION


class TestMedicationLimitValidator:
    """Tests for MedicationLimitValidator."""

    @pytest.mark.asyncio
    async def test_within_limit_passes(self):
        """Test that prescriptions within limit pass."""
        validator = MedicationLimitValidator(limit=5)
        data = {
            "patient_name": "Test Patient",
            "age": 30,
            "gender": "Male",
            "diagnosis": "Test",
            "icd_code": "J20.9",
            "provider_id": "DR-001",
            "medications": ["Med1", "Med2", "Med3"],
        }
        results = await validator.validate(data)
        assert len(results) == 0  # No flags

    @pytest.mark.asyncio
    async def test_exceeds_limit_flagged(self):
        """Test that prescriptions exceeding limit are flagged."""
        validator = MedicationLimitValidator(limit=5)
        data = {
            "patient_name": "Test Patient",
            "age": 30,
            "gender": "Male",
            "diagnosis": "Test",
            "icd_code": "J20.9",
            "provider_id": "DR-001",
            "medications": ["Med1", "Med2", "Med3", "Med4", "Med5", "Med6"],
        }
        results = await validator.validate(data)
        assert len(results) == 1
        assert results[0].status == ItemStatus.PENDING_REVIEW


class TestMedicationDurationValidator:
    """Tests for MedicationDurationValidator."""

    @pytest.mark.asyncio
    async def test_all_medications_pass_without_history(self):
        """Test that all medications pass without history data."""
        validator = MedicationDurationValidator(min_days=14)
        data = {
            "patient_name": "Test Patient",
            "age": 30,
            "gender": "Male",
            "diagnosis": "Test",
            "icd_code": "J20.9",
            "provider_id": "DR-001",
            "medications": ["Med1", "Panadol"],
        }
        results = await validator.validate(data)
        assert len(results) == 2
        for result in results:
            assert result.status == ItemStatus.APPROVED
            assert "No prior history" in result.duration_check
