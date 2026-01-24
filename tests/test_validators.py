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
    """Create sample input for testing."""
    return ExtractedOCRInput(
        patient_id="PAT-10023",
        patient_name="Ahmed Hassan",
        age=45,
        gender="Male",
        diagnosis="Acute Bronchitis",
        icd_code="J20.9",
        provider_id="DR-5501",
        medications=["Azithromycin 500mg", "Propranolol", "Panadol Extra"],
        labs=["Chest X-Ray"],
        medication_history={"Panadol Extra": 10},
        insurance_tier="Gold",
    )


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
    async def test_valid_lab_approved(self, sample_input: ExtractedOCRInput):
        """Test that valid labs are approved."""
        validator = ClinicalMatchValidator()
        results = await validator.validate(sample_input)

        # Chest X-Ray should be approved for Acute Bronchitis
        xray_result = next(
            r for r in results if "Chest X-Ray" in r.item_name
        )
        assert xray_result.status == ItemStatus.APPROVED
        assert xray_result.item_type == ItemType.LAB_ANALYSIS


class TestMedicationLimitValidator:
    """Tests for MedicationLimitValidator."""

    @pytest.mark.asyncio
    async def test_within_limit_passes(self):
        """Test that prescriptions within limit pass."""
        validator = MedicationLimitValidator(limit=5)
        data = ExtractedOCRInput(
            patient_id="PAT-001",
            patient_name="Test Patient",
            age=30,
            gender="Male",
            diagnosis="Test",
            icd_code="J20.9",
            provider_id="DR-001",
            medications=["Med1", "Med2", "Med3"],
        )
        results = await validator.validate(data)
        assert len(results) == 0  # No flags

    @pytest.mark.asyncio
    async def test_exceeds_limit_flagged(self):
        """Test that prescriptions exceeding limit are flagged."""
        validator = MedicationLimitValidator(limit=5)
        data = ExtractedOCRInput(
            patient_id="PAT-001",
            patient_name="Test Patient",
            age=30,
            gender="Male",
            diagnosis="Test",
            icd_code="J20.9",
            provider_id="DR-001",
            medications=["Med1", "Med2", "Med3", "Med4", "Med5", "Med6"],
        )
        results = await validator.validate(data)
        assert len(results) == 1
        assert results[0].status == ItemStatus.PENDING_REVIEW


class TestMedicationDurationValidator:
    """Tests for MedicationDurationValidator."""

    @pytest.mark.asyncio
    async def test_no_history_passes(self):
        """Test that medications without history pass."""
        validator = MedicationDurationValidator(min_days=14)
        data = ExtractedOCRInput(
            patient_id="PAT-001",
            patient_name="Test Patient",
            age=30,
            gender="Male",
            diagnosis="Test",
            icd_code="J20.9",
            provider_id="DR-001",
            medications=["Med1"],
            medication_history={},
        )
        results = await validator.validate(data)
        assert len(results) == 1
        assert results[0].status == ItemStatus.APPROVED

    @pytest.mark.asyncio
    async def test_too_soon_flagged(self):
        """Test that medications dispensed too recently are flagged."""
        validator = MedicationDurationValidator(min_days=14)
        data = ExtractedOCRInput(
            patient_id="PAT-001",
            patient_name="Test Patient",
            age=30,
            gender="Male",
            diagnosis="Test",
            icd_code="J20.9",
            provider_id="DR-001",
            medications=["Panadol"],
            medication_history={"Panadol": 10},  # 10 days ago
        )
        results = await validator.validate(data)
        assert len(results) == 1
        assert results[0].status == ItemStatus.FLAGGED
        assert results[0].duration_check == "FAILED"

    @pytest.mark.asyncio
    async def test_sufficient_time_passes(self):
        """Test that medications with sufficient time pass."""
        validator = MedicationDurationValidator(min_days=14)
        data = ExtractedOCRInput(
            patient_id="PAT-001",
            patient_name="Test Patient",
            age=30,
            gender="Male",
            diagnosis="Test",
            icd_code="J20.9",
            provider_id="DR-001",
            medications=["Panadol"],
            medication_history={"Panadol": 20},  # 20 days ago
        )
        results = await validator.validate(data)
        assert len(results) == 1
        assert results[0].status == ItemStatus.APPROVED
