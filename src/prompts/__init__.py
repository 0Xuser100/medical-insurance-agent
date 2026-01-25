"""Prompts package for LLM prompt engineering."""

from src.prompts.aggregator_prompt import (
    AGGREGATOR_CONFIG,
    SYSTEM_PROMPT,
    build_aggregation_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "build_aggregation_prompt",
    "AGGREGATOR_CONFIG",
]
