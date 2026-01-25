"""
LLM Aggregator Service.

Uses Gemini to synthesize OCR data and plain text agent validation results
into the final structured JSON response.

SOLID: Single Responsibility - only aggregates results via LLM.
SOLID: Dependency Inversion - depends on prompts module abstraction.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from loguru import logger

from src.models.schemas import (
    AIValidationEngine,
    ExtractedContext,
    ItemStatus,
    ItemType,
    LineItem,
    OverallStatus,
    PatientProfile,
    PrescriptionValidationResponse,
    RiskLevel,
    ValidationDetails,
)
from src.prompts.aggregator_prompt import (
    AGGREGATOR_CONFIG,
    SYSTEM_PROMPT,
    build_aggregation_prompt,
)

load_dotenv()


class LLMAggregatorService:
    """
    LLM-based aggregator that synthesizes validation results.

    Uses Gemini to combine OCR extraction data and plain text agent
    outputs into the final structured response.

    SOLID: Single Responsibility
    - Only responsible for LLM-based aggregation
    - Does not validate or extract data
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the LLM aggregator.

        Args:
            model_name: Gemini model to use (default from env GEMINI_MODEL_NAME)
        """
        self.model_name = model_name or os.getenv(
            "GEMINI_MODEL_NAME", "gemini-3-flash-preview"
        )
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        logger.info(f"LLMAggregatorService: Initialized with model {self.model_name}")

    def _clean_llm_response(self, response_text: str) -> str:
        """
        Clean LLM response to ensure valid JSON.

        Handles common LLM output issues:
        - Markdown code blocks (```json ... ```)
        - Leading/trailing whitespace
        - BOM characters
        - Empty field values (e.g., "field":  instead of "field": null)

        Args:
            response_text: Raw response from LLM

        Returns:
            Cleaned JSON string
        """
        import re

        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            # Remove opening ```json or ```
            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            # Remove closing ```
            text = re.sub(r"\n?```\s*$", "", text)

        # Remove BOM if present
        text = text.lstrip("\ufeff")

        # Fix empty field values: "field":  } or "field":  , → "field": null
        # This handles cases where LLM outputs nothing after the colon
        text = re.sub(r':\s*([,}\]])', r': null\1', text)

        # Fix trailing commas before closing brackets: ,} or ,]
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)

        return text.strip()

    def _safe_enum_parse(self, enum_class: type, value: Any, default: Any) -> Any:
        """
        Safely parse an enum value with fallback.

        Args:
            enum_class: The enum class to parse into
            value: The value to parse
            default: Default enum member if parsing fails

        Returns:
            Parsed enum member or default
        """
        if value is None:
            return default
        try:
            # Try direct match first
            return enum_class(value)
        except (ValueError, KeyError):
            try:
                # Try uppercase
                return enum_class(str(value).upper())
            except (ValueError, KeyError):
                logger.warning(
                    f"LLMAggregatorService: Invalid enum value '{value}' for {enum_class.__name__}, using default"
                )
                return default

    def _parse_llm_response(
        self, response_text: str, job_id: str
    ) -> PrescriptionValidationResponse:
        """
        Parse LLM JSON response into PrescriptionValidationResponse.

        Args:
            response_text: Raw JSON string from LLM
            job_id: Job ID to use as patient ID

        Returns:
            Validated PrescriptionValidationResponse object
        """
        # Clean the response first
        cleaned_response = self._clean_llm_response(response_text)

        try:
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Log more context for debugging
            logger.error(f"LLMAggregatorService: JSON parse error: {e}")
            logger.debug(f"LLMAggregatorService: Failed response (first 1000 chars): {cleaned_response[:1000]}")
            raise ValueError(f"Invalid JSON from LLM: {e}") from e

        # Build line items with safe parsing
        line_items = []
        for item in data.get("ai_validation_engine", {}).get("line_items", []):
            validation_details = item.get("validation_details", {})
            line_items.append(
                LineItem(
                    type=self._safe_enum_parse(
                        ItemType, item.get("type"), ItemType.MEDICATION
                    ),
                    item_name=str(item.get("item_name", "Unknown") or "Unknown"),
                    status=self._safe_enum_parse(
                        ItemStatus, item.get("status"), ItemStatus.PENDING_REVIEW
                    ),
                    ui_badge=str(item.get("ui_badge", "⏳ Pending") or "⏳ Pending"),
                    risk_level=self._safe_enum_parse(
                        RiskLevel, item.get("risk_level"), RiskLevel.LOW
                    ),
                    validation_details=ValidationDetails(
                        clinical_match=bool(validation_details.get("clinical_match", True)),
                        duration_check=validation_details.get("duration_check"),
                        reason_en=str(validation_details.get("reason_en", "") or ""),
                        reason_ar=str(validation_details.get("reason_ar", "") or ""),
                        linked_history_id=validation_details.get("linked_history_id"),
                    ),
                )
            )

        # Build patient profile with null safety - use job_id as patient ID
        patient_data = data.get("patient_profile", {}) or {}
        patient_profile = PatientProfile(
            id=job_id,  # Always use job_id as patient ID
            name=str(patient_data.get("name") or "Unknown"),
            age=str(patient_data.get("age") or "0"),
            gender=str(patient_data.get("gender") or "Unknown"),
            insurance_tier=str(patient_data.get("insurance_tier") or "Unknown"),
            history_summary=str(patient_data.get("history_summary") or ""),
        )

        # Build extracted context with null safety
        context_data = data.get("extracted_context", {}) or {}
        extracted_context = ExtractedContext(
            primary_diagnosis=str(context_data.get("primary_diagnosis") or "Unknown"),
            icd_code=str(context_data.get("icd_code") or "UNKNOWN"),
            provider_id=str(context_data.get("provider_id") or "Unknown"),
        )

        # Build AI validation engine with safe parsing
        engine_data = data.get("ai_validation_engine", {})
        confidence = engine_data.get("confidence_score", 0.0)
        if confidence is None:
            confidence = 0.0
        med_count = engine_data.get("medication_count", 0)
        if med_count is None:
            med_count = 0

        ai_validation_engine = AIValidationEngine(
            overall_status=self._safe_enum_parse(
                OverallStatus, engine_data.get("overall_status"), OverallStatus.REVIEW_NEEDED
            ),
            confidence_score=str(confidence),
            summary_message=str(
                engine_data.get("summary_message", "Validation completed.") or "Validation completed."
            ),
            medication_count=str(med_count),
            line_items=line_items,
        )

        return PrescriptionValidationResponse(
            transaction_id=data.get("transaction_id"),
            patient_profile=patient_profile,
            extracted_context=extracted_context,
            ai_validation_engine=ai_validation_engine,
        )

    async def aggregate(
        self,
        ocr_data: dict[str, Any],
        agent_text: str,
        job_id: str,
    ) -> PrescriptionValidationResponse:
        """
        Aggregate OCR data and plain text agent results into final response.

        Args:
            ocr_data: Extracted OCR data from prescription
            agent_text: Plain text output from validation agents
            job_id: Job ID to use as patient ID

        Returns:
            Complete PrescriptionValidationResponse
        """
        logger.info(
            f"LLMAggregatorService: Aggregating agent text for job {job_id}"
        )
        logger.debug(f"Agent text length: {len(agent_text)} chars")

        # Build the aggregation prompt with plain text
        prompt = build_aggregation_prompt(
            ocr_data=ocr_data,
            agent_text=agent_text,
        )

        # Call Gemini API
        try:
            response = await self._call_gemini(prompt)
            logger.debug(f"LLMAggregatorService: Raw response: {response[:500]}...")
        except Exception as e:
            logger.error(f"LLMAggregatorService: Gemini API error: {e}")
            raise

        # Parse and validate response
        result = self._parse_llm_response(response, job_id)
        logger.info(
            f"LLMAggregatorService: Aggregation complete - Status: {result.ai_validation_engine.overall_status.value}"
        )

        return result

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini API with the aggregation prompt.

        Args:
            prompt: Complete aggregation prompt

        Returns:
            Raw JSON response string
        """
        import asyncio

        def _sync_call() -> str:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=AGGREGATOR_CONFIG["temperature"],
                    max_output_tokens=AGGREGATOR_CONFIG["max_output_tokens"],
                    response_mime_type=AGGREGATOR_CONFIG["response_mime_type"],
                ),
            )
            return response.text

        # Run synchronous Gemini call in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_call)
