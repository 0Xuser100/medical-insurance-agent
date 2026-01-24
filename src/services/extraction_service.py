"""
Extraction Service.

Uses Google GenAI (Gemini) to extract prescription data from images/PDFs.

SOLID: Single Responsibility - only handles OCR extraction.
"""

import asyncio
import json
import os
import re
from pathlib import Path

import aiofiles
from google import genai
from google.genai import types
from loguru import logger

from src.models.schemas import ExtractedOCRInput


def _repair_json(text: str) -> str:
    """Attempt to repair common JSON issues from LLM responses."""
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Fix single quotes to double quotes (basic)
    # Only if no double quotes present in the value
    text = re.sub(r"(?<!\\)'([^']*)'(?=\s*[,:\]}])", r'"\1"', text)
    return text


EXTRACTION_PROMPT = """
Analyze the provided medical prescription image and extract all visible data.
Return ONLY a valid JSON object containing the extracted information.
No markdown, no triple backticks, no explanations.
"""


# MIME type mapping for file extensions
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".pdf": "application/pdf",
}


class ExtractionService:
    """
    Extracts prescription data from images/PDFs using Gemini.

    SOLID: Single Responsibility - OCR extraction only.
    """

    def __init__(self, model: str | None = None):
        """
        Initialize extraction service.

        Uses Gemini API with API key authentication.
        Requires:
            - GEMINI_API_KEY: Gemini API key

        Args:
            model: Gemini model to use for extraction (default from GEMINI_MODEL_NAME env)
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model = model or os.environ.get("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
        logger.info(f"ExtractionService initialized with model: {self.model}")

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type from file extension."""
        ext = file_path.suffix.lower()
        mime_type = MIME_TYPES.get(ext)
        if not mime_type:
            raise ValueError(f"Unsupported file type: {ext}")
        return mime_type

    def _extract_sync(self, file_path: Path, save_path: Path | None = None) -> dict:
        """
        Synchronous extraction - runs in a thread pool to avoid blocking.

        This mirrors the working test_gemini.py implementation.
        """
        logger.info(f"Starting sync extraction from file: {file_path}")

        # 1. Load file bytes
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        logger.debug(f"Loaded file bytes: {len(file_bytes)} bytes")

        # 2. Get MIME type
        mime_type = self._get_mime_type(file_path)
        logger.debug(f"MIME type: {mime_type}")

        # 3. Create fresh client (avoids thread-safety issues with reused client)
        api_key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        # 4. Call Gemini with image + prompt (sync)
        logger.info(f"Sending to Gemini model: {self.model}")
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                        types.Part.from_text(text=EXTRACTION_PROMPT),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        logger.info("Received response from Gemini")

        # 5. Parse JSON response
        json_text = response.text.strip()
        logger.debug(f"Raw response length: {len(json_text)} chars")

        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            json_text = "\n".join(lines[1:-1])
            logger.debug("Removed markdown code blocks from response")

        # Try parsing, with repair fallback
        try:
            data = json.loads(json_text)
            logger.info("Successfully parsed JSON response")
        except json.JSONDecodeError:
            logger.warning("JSON parse failed, attempting repair")
            repaired = _repair_json(json_text)
            try:
                data = json.loads(repaired)
                logger.info("Successfully parsed repaired JSON")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response: {e}")
                logger.error(f"Raw response (first 500 chars): {json_text[:500]}")
                raise ValueError(
                    f"Failed to parse Gemini response as JSON: {e}\n"
                    f"Raw response (first 500 chars): {json_text[:500]}"
                ) from e

        # 6. Save to disk if path provided
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved extracted data to: {save_path}")

        logger.info(f"Extraction complete. Data keys: {list(data.keys())}")
        return data

    async def extract_from_file(
        self,
        file_path: Path,
        save_path: Path | None = None,
    ) -> ExtractedOCRInput:
        """
        Extract prescription data from an image or PDF file.

        Args:
            file_path: Path to the image/PDF file
            save_path: Optional path to save extracted JSON

        Returns:
            ExtractedOCRInput with extracted data

        Raises:
            ValueError: If file type is unsupported
            Exception: If extraction fails
        """
        # Run sync extraction in thread pool to avoid blocking event loop
        return await asyncio.to_thread(self._extract_sync, file_path, save_path)
