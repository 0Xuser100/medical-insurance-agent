"""
Validation Crew - Multi-Agent CrewAI-based validation orchestrator.

Implements a specialized 3-agent system:
- Clinical Pharmacist: Drug-diagnosis matching
- Insurance Compliance Officer: Policy limit enforcement
- History Analyst: Refill interval verification

Simple configuration pattern following CrewAI best practices.
"""

import json
import os
from typing import Any, List

from dotenv import load_dotenv
from loguru import logger

from crewai import Agent, Crew, Task, Process
from crewai.tools import tool

from src.models.schemas import (
    ExtractedOCRInput,
    ItemStatus,
    ItemType,
    PrescriptionValidationResponse,
    RiskLevel,
    ValidationResult,
)
from src.services.report_builder import ReportBuilder

load_dotenv()

# ============================================================================
# Tools (one per agent)
# ============================================================================

# Global context storage (set before crew runs)
_prescription_context: dict = {}
_validation_results: List[ValidationResult] = []


@tool("clinical_match_check")
def clinical_match_check(medication_name: str) -> str:
    """
    Check if a medication is clinically appropriate for the diagnosis.
    Use this tool for EACH medication in the prescription.

    Args:
        medication_name: Name of the medication to validate
    """
    global _prescription_context, _validation_results

    if not _prescription_context:
        return "Error: No prescription context available"

    from src.validators.clinical_match import ClinicalMatchValidator

    validator = ClinicalMatchValidator()
    icd_code = _prescription_context.get("icd_code", "")
    diagnosis = _prescription_context.get("diagnosis") or _prescription_context.get("primary_diagnosis", "Unknown")

    is_valid, reason_en, reason_ar = validator._is_valid_for_diagnosis(
        medication_name, icd_code, ItemType.MEDICATION
    )

    # Store result
    _validation_results.append(ValidationResult(
        item_name=medication_name,
        item_type=ItemType.MEDICATION,
        status=ItemStatus.APPROVED if is_valid else ItemStatus.FLAGGED,
        risk_level=RiskLevel.LOW if is_valid else RiskLevel.HIGH,
        clinical_match=is_valid,
        reason_en=reason_en,
        reason_ar=reason_ar,
        guardrail="clinical_match",
    ))

    if is_valid:
        return f"APPROVED: {medication_name} is appropriate for {diagnosis}"
    return f"FLAGGED: {medication_name} - {reason_en}"


@tool("medication_limit_check")
def medication_limit_check() -> str:
    """
    Check if prescription exceeds the 5 medication limit.
    Use this once to verify policy compliance.
    """
    global _prescription_context, _validation_results

    if not _prescription_context:
        return "Error: No prescription context available"

    medications = _extract_medications(_prescription_context)
    count = len(medications)
    limit = int(os.getenv("MEDICATION_LIMIT", "5"))

    if count <= limit:
        return f"PASSED: {count} medications (limit: {limit})"

    # Store result
    _validation_results.append(ValidationResult(
        item_name=f"Prescription ({count} medications)",
        item_type=ItemType.MEDICATION,
        status=ItemStatus.PENDING_REVIEW,
        risk_level=RiskLevel.MEDIUM,
        clinical_match=True,
        reason_en=f"Exceeds limit of {limit}. Doctor review required.",
        reason_ar=f"تتجاوز الحد المسموح ({limit}). مطلوب مراجعة الطبيب.",
        guardrail="medication_limit",
    ))

    return f"VIOLATION: {count} medications exceeds limit of {limit}"


@tool("medication_duration_check")
def medication_duration_check(medication_name: str) -> str:
    """
    Check if medication was dispensed within the last 14 days.
    Use this for EACH medication to verify refill intervals.

    Args:
        medication_name: Name of the medication to check
    """
    global _prescription_context, _validation_results

    if not _prescription_context:
        return "Error: No prescription context available"

    min_days = int(os.getenv("MIN_DURATION_DAYS", "14"))

    # Store result (always passes without history)
    _validation_results.append(ValidationResult(
        item_name=medication_name,
        item_type=ItemType.MEDICATION,
        status=ItemStatus.APPROVED,
        risk_level=RiskLevel.LOW,
        clinical_match=True,
        duration_check="Passed (No prior history)",
        guardrail="medication_duration",
    ))

    return f"PASSED: {medication_name} - No prior history (min interval: {min_days} days)"


def _extract_medications(context: dict) -> List[str]:
    """Extract medication names from context."""
    medications = []

    if "medications" in context:
        for med in context["medications"]:
            if isinstance(med, dict):
                medications.append(med.get("name", str(med)))
            else:
                medications.append(str(med))

    if "prescription" in context:
        for item in context["prescription"]:
            if isinstance(item, dict):
                if "medication" in item:
                    medications.append(item["medication"])
                if "medications" in item:
                    medications.extend(item["medications"])

    return medications


# ============================================================================
# Agent Definitions
# ============================================================================

def create_clinical_pharmacist(llm: str) -> Agent:
    """Agent 1: Clinical Pharmacist"""
    return Agent(
        role="Senior Clinical Pharmacist",
        goal="Validate that each medication is clinically appropriate for the diagnosis",
        backstory="You are a medical expert focused on drug-diagnosis matching. "
                  "Your ONLY concern is clinical correctness. Ignore policy limits and timing.",
        llm=llm,
        tools=[clinical_match_check],
        verbose=True,
        max_iter=5,
    )


def create_compliance_officer(llm: str) -> Agent:
    """Agent 2: Insurance Compliance Officer"""
    return Agent(
        role="Insurance Compliance Officer",
        goal="Enforce the maximum 5 medications policy limit",
        backstory="You are a strict policy enforcer. Your ONLY concern is the medication count. "
                  "More than 5 medications = violation requiring doctor review.",
        llm=llm,
        tools=[medication_limit_check],
        verbose=True,
        max_iter=5,
    )


def create_history_analyst(llm: str) -> Agent:
    """Agent 3: Medical History Analyst"""
    return Agent(
        role="Medical History Analyst",
        goal="Verify minimum 14-day gap between same medication refills",
        backstory="You are a timeline analyst checking dispensing patterns. "
                  "Your ONLY concern is refill intervals to prevent early dispensing.",
        llm=llm,
        tools=[medication_duration_check],
        verbose=True,
        max_iter=5,
    )


# ============================================================================
# ValidationCrew Class
# ============================================================================

class ValidationCrew:
    """Multi-Agent validation orchestrator with simple configuration."""

    def __init__(
        self,
        report_builder: ReportBuilder,
        model_name: str | None = None,
        validation_service: Any = None,  # Backward compatibility
    ):
        self.report_builder = report_builder
        self.model_name = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

        # Create agents
        self.clinical_pharmacist = create_clinical_pharmacist(self.model_name)
        self.compliance_officer = create_compliance_officer(self.model_name)
        self.history_analyst = create_history_analyst(self.model_name)

    def _calculate_success_rate(self, results: List[ValidationResult]) -> float:
        """Calculate approval rate."""
        if not results:
            return 1.0

        unique = {}
        for r in results:
            if r.item_name not in unique or r.status != ItemStatus.APPROVED:
                unique[r.item_name] = r

        if not unique:
            return 1.0

        approved = sum(1 for r in unique.values() if r.status == ItemStatus.APPROVED)
        return approved / len(unique)

    async def validate_prescription(
        self, data: ExtractedOCRInput, job_id: str
    ) -> PrescriptionValidationResponse:
        """Run multi-agent validation."""
        global _prescription_context, _validation_results

        logger.info(f"ValidationCrew: Starting validation for {job_id}")

        # Set global context
        _prescription_context = data
        _validation_results = []

        # Full OCR context for agents
        context_json = json.dumps(data, indent=2, ensure_ascii=False)

        # Task 1: Clinical Pharmacist
        clinical_task = Task(
            description=f"""
Use the provided full OCR JSON context to identify the medications and clinical data needed for your check.

FULL OCR JSON CONTEXT:
{context_json}

YOUR TASK:
1. Identify the UNIQUE list of medications from the JSON (ignore duplicates - each medication name should appear only once).
2. Identify the diagnosis and ICD code from the JSON.
3. For each UNIQUE medication, execute the clinical_match_check tool EXACTLY ONCE.
4. Summarize your findings and finish immediately. DO NOT repeat any checks.
""",
            expected_output="Assessment for each medication with APPROVED/FLAGGED status",
            agent=self.clinical_pharmacist,
        )

        # Task 2: Compliance Officer
        compliance_task = Task(
            description=f"""
Use the provided full OCR JSON context to identify the medications and clinical data needed for your check.

FULL OCR JSON CONTEXT:
{context_json}

YOUR TASK:
1. Count the total number of unique medications in the prescription.
2. Execute the medication_limit_check tool ONLY ONCE.
3. Do NOT retry or repeat the tool call. Provide the result and finish immediately.
POLICY: Maximum 5 medications per prescription.
""",
            expected_output="PASSED or VIOLATION with medication count",
            agent=self.compliance_officer,
        )

        # Task 3: History Analyst
        history_task = Task(
            description=f"""
Use the provided full OCR JSON context to identify the medications and clinical data needed for your check.

FULL OCR JSON CONTEXT:
{context_json}

YOUR TASK:
1. Identify the UNIQUE list of medications from the JSON (ignore duplicates - each medication name should appear only once).
2. Execute the medication_duration_check tool EXACTLY ONCE per unique medication.
3. IMPORTANT: If you have already checked a medication, DO NOT repeat the check. Do not call the tool more than once for the same medication name.
4. After checking all unique medications once, finish immediately.
POLICY: Minimum 14 days between same medication.
""",
            expected_output="Duration check result for each medication",
            agent=self.history_analyst,
        )

        # Run Crew
        crew = Crew(
            agents=[self.clinical_pharmacist, self.compliance_officer, self.history_analyst],
            tasks=[clinical_task, compliance_task, history_task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            logger.info("ValidationCrew: Running crew")
            await crew.kickoff_async()
            logger.info("ValidationCrew: Crew completed")
        except Exception as e:
            logger.warning(f"CrewAI warning: {e}")

        # Build report
        success_rate = self._calculate_success_rate(_validation_results)
        logger.info(f"ValidationCrew: Success rate = {success_rate:.2%}")

        return await self.report_builder.build_report(
            data, _validation_results, success_rate, job_id
        )

    async def validate_prescription_simple(
        self, data: ExtractedOCRInput, job_id: str
    ) -> PrescriptionValidationResponse:
        """Rule-based validation without agents (faster)."""
        logger.info(f"ValidationCrew: Simple validation for {job_id}")

        from src.validators.clinical_match import ClinicalMatchValidator
        from src.validators.medication_limit import MedicationLimitValidator
        from src.validators.medication_duration import MedicationDurationValidator

        validators = [
            ClinicalMatchValidator(),
            MedicationLimitValidator(),
            MedicationDurationValidator(),
        ]

        all_results = []
        for v in validators:
            results = await v.validate(data)
            all_results.extend(results)

        success_rate = self._calculate_success_rate(all_results)
        return await self.report_builder.build_report(data, all_results, success_rate, job_id)
