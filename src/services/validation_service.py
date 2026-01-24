"""
Validation Service.

Orchestrates all validators and runs them concurrently.

SOLID: Dependency Inversion - depends on ValidatorProtocol, not concrete classes.
"""

import asyncio
from typing import Sequence

from src.core.protocols import ValidatorProtocol
from src.models.schemas import ExtractedOCRInput, ValidationResult


class ValidationService:
    """
    Orchestrates validators.

    SOLID: Dependency Inversion
    - Accepts validators via constructor injection
    - Depends on ValidatorProtocol abstraction
    """

    def __init__(self, validators: Sequence[ValidatorProtocol]):
        """
        Initialize the validation service.

        Args:
            validators: List of validators to run
        """
        self.validators = list(validators)

    async def run_all_validations(
        self, data: ExtractedOCRInput
    ) -> list[ValidationResult]:
        """
        Run all validators concurrently.

        Args:
            data: Extracted OCR input data

        Returns:
            Flattened list of all validation results
        """
        # Run all validators concurrently
        tasks = [validator.validate(data) for validator in self.validators]
        results = await asyncio.gather(*tasks)

        # Flatten results
        return [result for sublist in results for result in sublist]

    async def run_single_validation(
        self, validator: ValidatorProtocol, data: ExtractedOCRInput
    ) -> list[ValidationResult]:
        """
        Run a single validator.

        Args:
            validator: The validator to run
            data: Extracted OCR input data

        Returns:
            List of validation results from this validator
        """
        return await validator.validate(data)
