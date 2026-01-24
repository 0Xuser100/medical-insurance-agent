"""
Report Builder Service.

Builds the final JSON response from validation results.

SOLID: Single Responsibility - only builds reports.
"""

from loguru import logger

from src.models.schemas import (
    AIValidationEngine,
    ExtractedContext,
    ExtractedOCRInput,
    ItemStatus,
    LineItem,
    OverallStatus,
    PatientProfile,
    PrescriptionValidationResponse,
    RiskLevel,
    ValidationDetails,
    ValidationResult,
)


class ReportBuilder:
    """
    Builds final prescription validation response.

    SOLID: Single Responsibility
    - Only responsible for building the JSON response
    - Does not validate or modify data
    """

    def _get_ui_badge(self, result: ValidationResult) -> str:
        """Generate UI badge text based on validation result."""
        if result.status == ItemStatus.APPROVED:
            return "Auto-Approved"
        elif result.status == ItemStatus.PENDING_REVIEW:
            return "Doctor Review Needed"
        elif not result.clinical_match:
            return "Safety Alert"
        elif result.duration_check == "FAILED":
            return "Rejected - Too Soon"
        else:
            return "Flagged"

    def _determine_overall_status(
        self, results: list[ValidationResult]
    ) -> OverallStatus:
        """Determine overall status based on all validation results."""
        if not results:
            return OverallStatus.APPROVED

        has_flagged = any(r.status == ItemStatus.FLAGGED for r in results)
        has_pending = any(r.status == ItemStatus.PENDING_REVIEW for r in results)
        all_approved = all(r.status == ItemStatus.APPROVED for r in results)

        if all_approved:
            return OverallStatus.APPROVED
        elif has_flagged or has_pending:
            return OverallStatus.REVIEW_NEEDED
        else:
            return OverallStatus.APPROVED

    def _generate_summary_message(
        self, results: list[ValidationResult], success_rate: float
    ) -> str:
        """Generate summary message for the response."""
        total = len(results)
        approved = sum(1 for r in results if r.status == ItemStatus.APPROVED)
        flagged = sum(1 for r in results if r.status == ItemStatus.FLAGGED)
        pending = sum(1 for r in results if r.status == ItemStatus.PENDING_REVIEW)

        parts = []

        if approved == total:
            return "All items approved. Prescription validated successfully."

        if approved > 0:
            parts.append(f"{approved} item(s) approved")

        if flagged > 0:
            parts.append(f"{flagged} item(s) flagged")

        if pending > 0:
            parts.append(f"{pending} item(s) require doctor review")

        return "Request partially approved. " + ". ".join(parts) + "."

    def _merge_results_by_item(
        self, results: list[ValidationResult]
    ) -> dict[str, ValidationResult]:
        """
        Merge multiple results for the same item.

        If an item has multiple results (from different validators),
        use the worst status.
        """
        merged: dict[str, ValidationResult] = {}

        status_priority = {
            ItemStatus.FLAGGED: 0,
            ItemStatus.PENDING_REVIEW: 1,
            ItemStatus.APPROVED: 2,
        }

        for result in results:
            key = result.item_name

            if key not in merged:
                merged[key] = result
            else:
                existing = merged[key]
                # Keep the result with worse (lower priority) status
                if status_priority[result.status] < status_priority[existing.status]:
                    # Merge reason fields
                    merged[key] = ValidationResult(
                        item_name=result.item_name,
                        item_type=result.item_type,
                        status=result.status,
                        risk_level=max(result.risk_level, existing.risk_level, key=lambda x: ["LOW", "MEDIUM", "HIGH"].index(x.value)),
                        clinical_match=result.clinical_match and existing.clinical_match,
                        duration_check=result.duration_check or existing.duration_check,
                        reason_en=result.reason_en or existing.reason_en,
                        reason_ar=result.reason_ar or existing.reason_ar,
                        linked_history_id=result.linked_history_id or existing.linked_history_id,
                        guardrail=result.guardrail,
                    )
                elif result.duration_check and not existing.duration_check:
                    # Add duration check to existing
                    merged[key] = ValidationResult(
                        item_name=existing.item_name,
                        item_type=existing.item_type,
                        status=existing.status,
                        risk_level=existing.risk_level,
                        clinical_match=existing.clinical_match,
                        duration_check=result.duration_check,
                        reason_en=existing.reason_en,
                        reason_ar=existing.reason_ar,
                        linked_history_id=existing.linked_history_id or result.linked_history_id,
                        guardrail=existing.guardrail,
                    )

        return merged

    async def build_report(
        self,
        data: ExtractedOCRInput,
        validation_results: list[ValidationResult],
        success_rate: float,
        job_id: str,
    ) -> PrescriptionValidationResponse:
        """
        Build the complete prescription validation response.

        Args:
            data: Original extracted OCR input
            validation_results: Results from all validators
            success_rate: Percentage of approved items (0.0 to 1.0)
            job_id: Job ID to use as patient ID (PAT-xxx format)

        Returns:
            Complete prescription validation response
        """
        logger.info(f"ReportBuilder: Building report for job {job_id}")

        # Merge results for same items
        merged_results = self._merge_results_by_item(validation_results)
        results_list = list(merged_results.values())
        logger.debug(f"Merged {len(validation_results)} results into {len(results_list)} unique items")

        # Build line items
        line_items: list[LineItem] = []
        for result in results_list:
            # Skip prescription-level results (from medication limit)
            if "Prescription (" in result.item_name:
                continue

            line_item = LineItem(
                type=result.item_type,
                item_name=result.item_name,
                status=result.status,
                ui_badge=self._get_ui_badge(result),
                risk_level=result.risk_level,
                validation_details=ValidationDetails(
                    clinical_match=result.clinical_match,
                    duration_check=result.duration_check,
                    reason_en=result.reason_en,
                    reason_ar=result.reason_ar,
                    linked_history_id=result.linked_history_id,
                ),
            )
            line_items.append(line_item)

        # Determine overall status
        overall_status = self._determine_overall_status(results_list)

        # Check for medication limit flag
        for result in results_list:
            if result.guardrail == "medication_limit" and result.status == ItemStatus.PENDING_REVIEW:
                overall_status = OverallStatus.REVIEW_NEEDED
                break

        logger.info(f"ReportBuilder: Overall status = {overall_status.value}, Success rate = {success_rate:.2%}")

        # Extract fields with fallbacks (Gemini may use different field names)
        patient_name = data.get("patient_name") or data.get("patient_information", {}).get("name", "Unknown")
        age = data.get("age") or data.get("patient_information", {}).get("age", 0)
        gender = data.get("gender") or data.get("patient_information", {}).get("gender", "Unknown")
        diagnosis = data.get("diagnosis") or data.get("primary_diagnosis", "Unknown")
        icd_code = data.get("icd_code", "")
        provider_id = data.get("provider_id") or data.get("doctor_information", {}).get("id", "Unknown")
        medications = data.get("medications", [])

        # Ensure age is an integer
        if isinstance(age, str):
            try:
                age = int(age.split()[0])  # Handle "45 years" format
            except (ValueError, IndexError):
                age = 0

        # Build response - use job_id as patient_id
        return PrescriptionValidationResponse(
            patient_profile=PatientProfile(
                id=job_id,  # Use job_id (PAT-xxx) as patient ID
                name=patient_name,
                age=age,
                gender=gender,
                insurance_tier="Unknown",  # Not extracted from prescription
                history_summary="",  # Not available in MVP
            ),
            extracted_context=ExtractedContext(
                primary_diagnosis=diagnosis,
                icd_code=icd_code,
                provider_id=provider_id,
            ),
            ai_validation_engine=AIValidationEngine(
                overall_status=overall_status,
                confidence_score=success_rate,
                summary_message=self._generate_summary_message(results_list, success_rate),
                medication_count=len(medications),
                line_items=line_items,
            ),
        )
