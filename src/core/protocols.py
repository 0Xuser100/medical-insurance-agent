"""
Core protocols for dependency inversion.

SOLID Principles:
- D: Dependency Inversion - depend on abstractions
- I: Interface Segregation - specific interfaces for each responsibility
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.models.schemas import (
        ExtractedOCRInput,
        PrescriptionValidationResponse,
        ValidationResult,
    )


@runtime_checkable
class ValidatorProtocol(Protocol):
    """
    Interface for all validators.

    SOLID: Interface Segregation - each validator only needs to implement validate().
    """

    async def validate(self, data: "ExtractedOCRInput") -> list["ValidationResult"]:
        """
        Validate extracted OCR data and return validation results.

        Args:
            data: Extracted OCR input data

        Returns:
            List of validation results for each item checked
        """
        ...


@runtime_checkable
class ReportBuilderProtocol(Protocol):
    """
    Interface for report building.

    SOLID: Single Responsibility - only builds reports.
    """

    async def build_report(
        self,
        data: "ExtractedOCRInput",
        validation_results: list["ValidationResult"],
        success_rate: float,
    ) -> "PrescriptionValidationResponse":
        """
        Build final prescription validation response.

        Args:
            data: Original extracted OCR input
            validation_results: Results from all validators
            success_rate: Percentage of approved items

        Returns:
            Complete prescription validation response
        """
        ...
