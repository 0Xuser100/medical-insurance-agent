"""
LangChain-based Validation Service.

Replaces CrewAI multi-agent system with single Gemini call.
Uses Gemini native structured output for guaranteed schema compliance.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
from pydantic import BaseModel, Field

from src.models.schemas import (
    PrescriptionValidationResponse,
    AIValidationEngine,
    PatientProfile,
    LineItem,
    ValidationDetails,
    ItemType,
    ItemStatus,
    RiskLevel,
    OverallStatus,
)
from src.prompts.aggregator_prompt import UNIFIED_VALIDATION_PROMPT

load_dotenv()


class ValidationLineItem(BaseModel):
    """Schema for a single validated line item."""

    type: str = Field(description="Item type: MEDICATION, LAB_ANALYSIS, RADIOLOGY, or PROCEDURE")
    item_name: str = Field(description="Name of the medication or procedure")
    status: str = Field(description="Validation status: APPROVED, REVIEW_NEEDED, or REJECTED")
    ui_badge: str = Field(description="UI display badge")
    risk_level: str = Field(description="Risk level: LOW, MEDIUM, or HIGH")
    clinical_match: bool = Field(description="Whether item matches diagnosis")
    duration_check: str | None = Field(default=None, description="Duration check result")
    reason_en: str = Field(description="Reason in English")
    reason_ar: str = Field(description="Reason in Arabic")


class ValidationOutputSchema(BaseModel):
    """Complete validation output schema for Gemini native structured output."""

    patient_name: str = Field(description="Patient name from prescription")
    patient_age: str = Field(description="Patient age")
    patient_gender: str = Field(description="Patient gender")
    overall_status: str = Field(description="Overall status: APPROVED, REVIEW_NEEDED, or REJECTED")
    confidence_score: float = Field(description="Confidence score 0.0 to 1.0")
    line_items: list[ValidationLineItem] = Field(description="Validated line items")


class LangChainValidationService:
    """
    Unified validation service using LangChain + Gemini.

    Replaces:
    - ValidationCrew (CrewAI agents)
    - LLMAggregatorService (Gemini aggregation)
    - Individual validators (clinical_match, medication_limit, medication_duration)
    """

    def __init__(
        self,
        model_name: str | None = None,
        mappings_path: Path | None = None,
        medication_history_path: Path | None = None,
        medication_limit: int | None = None,
        min_duration_days: int | None = None,
    ):
        self.model_name = model_name or "gemini-2.5-flash-preview-09-2025"
        self.medication_limit = medication_limit or int(os.getenv("MEDICATION_LIMIT", "5"))
        self.min_duration_days = min_duration_days or int(os.getenv("MIN_DURATION_DAYS", "14"))

        # Load diagnosis mappings
        if mappings_path is None:
            mappings_path = Path(__file__).parent.parent / "data" / "diagnosis_mappings.json"
        self.diagnosis_mappings = self._load_mappings(mappings_path)

        # Load patient medication history for duration check
        if medication_history_path is None:
            medication_history_path = Path(__file__).parent.parent / "data" / "patient_medication_history.json"
        self.patient_medication_history = self._load_mappings(medication_history_path)

        # Initialize LangChain components with native structured output
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        # Use Gemini's native structured output - schema enforced at token generation level
        self.structured_llm = self.llm.with_structured_output(ValidationOutputSchema)
        self.prompt = self._build_prompt_template()

        logger.info(f"LangChainValidationService initialized with model: {self.model_name} (native structured output)")

    def _load_mappings(self, path: Path) -> dict:
        """Load diagnosis mappings from JSON file."""
        if not path.exists():
            logger.warning(f"Mappings file not found: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_prompt_template(self) -> PromptTemplate:
        """Build the unified validation prompt template."""
        return PromptTemplate(
            template=UNIFIED_VALIDATION_PROMPT,
            input_variables=["ocr_data", "diagnosis_mappings", "patient_medication_history", "medication_limit", "min_duration_days", "job_id"],
        )

    async def validate_prescription(
        self,
        ocr_data: dict[str, Any],
        job_id: str,
    ) -> PrescriptionValidationResponse:
        """
        Validate prescription data using Gemini via LangChain.

        Args:
            ocr_data: Extracted OCR data from prescription
            job_id: Job ID (used as patient ID)

        Returns:
            PrescriptionValidationResponse with validated line items
        """
        logger.info(f"LangChainValidationService: Validating prescription for job {job_id}")

        # Format the prompt
        formatted_prompt = self.prompt.format(
            ocr_data=json.dumps(ocr_data, indent=2, ensure_ascii=False),
            diagnosis_mappings=json.dumps(self.diagnosis_mappings, indent=2, ensure_ascii=False),
            patient_medication_history=json.dumps(self.patient_medication_history, indent=2, ensure_ascii=False),
            medication_limit=self.medication_limit,
            min_duration_days=self.min_duration_days,
            job_id=job_id,
        )

        # Invoke LLM with native structured output
        try:
            result: ValidationOutputSchema = await self._invoke_structured_llm(formatted_prompt)
            logger.info("LangChainValidationService: Received structured response")
        except Exception as e:
            logger.error(f"LangChainValidationService: LLM error: {e}")
            raise

        # Convert to PrescriptionValidationResponse
        return self._build_response(result, ocr_data, job_id)

    async def _invoke_structured_llm(self, prompt: str) -> ValidationOutputSchema:
        """Invoke the structured LLM with the formatted prompt."""
        # ChatGoogleGenerativeAI.invoke is sync, wrap in thread
        logger.info(f"Sending to Gemini model: {self.model_name}")
        result = await asyncio.to_thread(self.structured_llm.invoke, prompt)
        logger.info("Received response from Gemini")
        return result

    def _safe_enum_parse(self, enum_class, value: str, default):
        """Safely parse enum value with fallback."""
        try:
            return enum_class(value)
        except (ValueError, KeyError):
            return default

    def _build_response(
        self,
        result: ValidationOutputSchema,
        ocr_data: dict,
        job_id: str,
    ) -> PrescriptionValidationResponse:
        """Convert structured LLM output to PrescriptionValidationResponse."""
        # Build line items from Pydantic model
        line_items = []
        for item in result.line_items:
            line_items.append(LineItem(
                type=self._safe_enum_parse(ItemType, item.type, ItemType.MEDICATION),
                item_name=item.item_name,
                status=self._safe_enum_parse(ItemStatus, item.status, ItemStatus.REVIEW_NEEDED),
                ui_badge=item.ui_badge,
                risk_level=self._safe_enum_parse(RiskLevel, item.risk_level, RiskLevel.LOW),
                validation_details=ValidationDetails(
                    clinical_match=item.clinical_match,
                    duration_check=item.duration_check,
                    reason_en=item.reason_en,
                    reason_ar=item.reason_ar,
                ),
            ))

        medications = ocr_data.get("medications", [])

        return PrescriptionValidationResponse(
            patient_profile=PatientProfile(
                id=job_id,
                name=result.patient_name,
                age=result.patient_age,
                gender=result.patient_gender,
            ),
            ai_validation_engine=AIValidationEngine(
                overall_status=self._safe_enum_parse(
                    OverallStatus, result.overall_status, OverallStatus.REVIEW_NEEDED
                ),
                confidence_score=str(result.confidence_score),
                medication_count=str(len(medications)),
                line_items=line_items,
            ),
        )
