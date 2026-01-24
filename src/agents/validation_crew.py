"""
Validation Crew - CrewAI-based validation orchestrator.

Implements the agent loop:
- GOAL: Validate prescription items
- THINK: Analyze extracted data
- TOOLS: Execute validation checks
- LOOP: Process all items
- SUCCESS RATE: Calculate confidence score

SOLID: Dependency Inversion - depends on injected services.
"""

import os
from typing import Any

from dotenv import load_dotenv

from crewai import Agent, Crew, Task
from crewai.tools import tool

from src.models.schemas import (
    ExtractedOCRInput,
    ItemStatus,
    PrescriptionValidationResponse,
)
from src.services.report_builder import ReportBuilder
from src.services.validation_service import ValidationService

# Load environment variables
load_dotenv()


class ValidationCrew:
    """
    CrewAI-based validation orchestrator.

    Agent Loop Structure:
    1. GOAL - Validate prescription and generate approval report
    2. THINK - Analyze extracted data, identify items to check
    3. TOOLS - Execute validation tools (3 guardrails)
    4. LOOP - Process all items until done
    5. SUCCESS RATE - Calculate confidence score
    """

    def __init__(
        self,
        validation_service: ValidationService,
        report_builder: ReportBuilder,
        model_name: str | None = None,
    ):
        """
        Initialize the validation crew.

        Args:
            validation_service: Service to orchestrate validators
            report_builder: Service to build final report
            model_name: OpenAI model name (default from env)
        """
        self.validation_service = validation_service
        self.report_builder = report_builder
        self.model_name = model_name or os.getenv("OPENAI_MODEL_NAME")

        # Store current data for tool access
        self._current_data: ExtractedOCRInput | None = None

        # Create tools
        self._create_tools()

        # Create agent with GOAL
        self.agent = self._create_agent()

    def _create_tools(self) -> None:
        """Create CrewAI tools for validation."""

        @tool("clinical_match_check")
        def clinical_match_check(item_name: str, item_type: str) -> str:
            """
            Check if a medication or lab is clinically appropriate for the diagnosis.

            Args:
                item_name: Name of the medication or lab test
                item_type: Either 'medication' or 'lab'

            Returns:
                Validation result as a string
            """
            if self._current_data is None:
                return "Error: No data available"

            from src.validators.clinical_match import ClinicalMatchValidator
            from src.models.schemas import ItemType

            validator = ClinicalMatchValidator()
            it = ItemType.MEDICATION if item_type.lower() == "medication" else ItemType.LAB_ANALYSIS

            is_valid, reason_en, _ = validator._is_valid_for_diagnosis(
                item_name, self._current_data.icd_code, it
            )

            if is_valid:
                return f"APPROVED: {item_name} is clinically appropriate for {self._current_data.diagnosis}"
            else:
                return f"FLAGGED: {reason_en}"

        @tool("medication_limit_check")
        def medication_limit_check() -> str:
            """
            Check if the prescription exceeds the 5 medication limit.

            Returns:
                Result indicating if the limit is exceeded
            """
            if self._current_data is None:
                return "Error: No data available"

            count = len(self._current_data.medications)
            limit = 5

            if count <= limit:
                return f"PASSED: Prescription has {count} medications (limit: {limit})"
            else:
                return f"FLAGGED: Prescription has {count} medications, exceeds limit of {limit}. Doctor review required."

        @tool("medication_duration_check")
        def medication_duration_check(medication_name: str) -> str:
            """
            Check if a medication was dispensed within the last 14 days.

            Args:
                medication_name: Name of the medication to check

            Returns:
                Result indicating if minimum duration is met
            """
            if self._current_data is None:
                return "Error: No data available"

            history = self._current_data.medication_history
            min_days = 14

            # Find matching medication in history
            for hist_med, days in history.items():
                if hist_med.lower() in medication_name.lower() or medication_name.lower() in hist_med.lower():
                    if days >= min_days:
                        return f"PASSED: {medication_name} was last dispensed {days} days ago (minimum: {min_days})"
                    else:
                        return f"FLAGGED: {medication_name} was dispensed {days} days ago. Minimum {min_days} days required."

            return f"PASSED: {medication_name} has no prior dispensing history"

        self.tools = [clinical_match_check, medication_limit_check, medication_duration_check]

    def _create_agent(self) -> Agent:
        """Create the validation agent with GOAL."""
        return Agent(
            role="Medical Insurance Validator",
            goal="Validate each prescription item against 3 guardrails and generate accurate approval report",
            backstory="""You are an expert medical insurance claims validator with deep knowledge of:
            - Clinical guidelines and drug-diagnosis matching
            - Polypharmacy risks and medication limits
            - Prescription refill policies and duration requirements

            Your job is to:
            1. Check if each medication/lab is clinically appropriate for the diagnosis
            2. Verify the prescription doesn't exceed medication limits
            3. Ensure minimum time between refills is respected

            You must generate bilingual explanations (English/Arabic) for any flagged items.
            Be thorough and accurate - patient safety depends on your validation.""",
            tools=self.tools,
            llm=self.model_name,
            verbose=True,
            allow_delegation=False,
        )

    def _calculate_success_rate(self, results: list) -> float:
        """
        Calculate SUCCESS RATE: approved items / total items.

        Args:
            results: List of validation results

        Returns:
            Success rate between 0.0 and 1.0
        """
        if not results:
            return 1.0

        approved = sum(1 for r in results if r.status == ItemStatus.APPROVED)
        return approved / len(results)

    async def validate_prescription(
        self, data: ExtractedOCRInput
    ) -> PrescriptionValidationResponse:
        """
        Validate a prescription using the agent loop.

        Agent Loop:
        1. GOAL - Set by agent creation
        2. THINK - Task description triggers analysis
        3. TOOLS - Agent uses validation tools
        4. LOOP - CrewAI handles iteration
        5. SUCCESS RATE - Calculated from results

        Args:
            data: Extracted OCR input data

        Returns:
            Complete prescription validation response
        """
        # Store data for tool access
        self._current_data = data

        # THINK: Create task with detailed prompt
        task = Task(
            description=f"""
            Validate this prescription and provide a comprehensive assessment:

            PATIENT INFORMATION:
            - ID: {data.patient_id}
            - Name: {data.patient_name}
            - Age: {data.age}
            - Gender: {data.gender}

            PRESCRIPTION DETAILS:
            - Diagnosis: {data.diagnosis} (ICD Code: {data.icd_code})
            - Provider: {data.provider_id}

            ITEMS TO VALIDATE:
            - Medications: {', '.join(data.medications) if data.medications else 'None'}
            - Labs: {', '.join(data.labs) if data.labs else 'None'}

            MEDICATION HISTORY:
            {data.medication_history if data.medication_history else 'No prior history'}

            VALIDATION STEPS:
            1. For EACH medication, use clinical_match_check to verify it's appropriate for the diagnosis
            2. Use medication_limit_check to verify total medication count
            3. For EACH medication, use medication_duration_check to verify refill timing

            Provide a summary of your findings.
            """,
            agent=self.agent,
            expected_output="""A detailed validation report including:
            - Status for each medication (APPROVED/FLAGGED)
            - Status for each lab (APPROVED/FLAGGED)
            - Medication limit check result
            - Duration check results
            - Overall recommendation""",
        )

        # LOOP: Create and run crew
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True,
        )

        # Execute the crew (this runs the Think → Tools → Loop)
        try:
            await crew.kickoff_async()
        except Exception as e:
            # Log error but continue with rule-based validation
            print(f"CrewAI execution warning: {e}")

        # Run rule-based validators as the source of truth
        validation_results = await self.validation_service.run_all_validations(data)

        # SUCCESS RATE: Calculate confidence
        success_rate = self._calculate_success_rate(validation_results)

        # Build final report
        return await self.report_builder.build_report(
            data, validation_results, success_rate
        )

    async def validate_prescription_simple(
        self, data: ExtractedOCRInput
    ) -> PrescriptionValidationResponse:
        """
        Validate prescription without CrewAI agent (rule-based only).

        Useful for faster validation when LLM reasoning isn't needed.

        Args:
            data: Extracted OCR input data

        Returns:
            Complete prescription validation response
        """
        # Run validators
        validation_results = await self.validation_service.run_all_validations(data)

        # Calculate success rate
        success_rate = self._calculate_success_rate(validation_results)

        # Build report
        return await self.report_builder.build_report(
            data, validation_results, success_rate
        )
