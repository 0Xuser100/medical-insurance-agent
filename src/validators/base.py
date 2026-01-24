"""
Base validator class.

SOLID Principles:
- O: Open/Closed - extend via inheritance, don't modify
- L: Liskov Substitution - all validators are interchangeable
"""

from abc import ABC, abstractmethod

from src.models.schemas import ExtractedOCRInput, ValidationResult


class BaseValidator(ABC):
    """
    Abstract base class for all validators.

    SOLID: Open/Closed Principle
    - Open for extension: create new validators by inheriting
    - Closed for modification: don't change this base class
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this validator."""
        ...

    @abstractmethod
    async def validate(self, data: ExtractedOCRInput) -> list[ValidationResult]:
        """
        Validate the extracted OCR data.

        Args:
            data: Extracted OCR input data

        Returns:
            List of validation results
        """
        ...
