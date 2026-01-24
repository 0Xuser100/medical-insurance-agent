"""
Extraction Service.

Uses Google GenAI (Gemini) to extract prescription data from images/PDFs.

SOLID: Single Responsibility - only handles OCR extraction.
"""

import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types

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
You are a medical prescription OCR extraction system. Analyze this prescription image/PDF and extract the following information as JSON.

Return ONLY valid JSON with this exact structure:
{
    "patient_name": "string - patient full name",
    "age": number - patient age (integer),
    "gender": "string - Male or Female",
    "diagnosis": "string - primary diagnosis description",
    "icd_code": "string - ICD-10 code if visible, otherwise infer from diagnosis (e.g., J20.9 for Acute Bronchitis)",
    "provider_id": "string - doctor/provider ID if visible, otherwise generate as DR-XXXXX",
    "medications": ["array of medication names with dosage"]
}

CRITICAL RULES:
- Return ONLY valid JSON - no markdown, no explanations, no extra text
- Extract ALL medications listed with their dosages
- If a field is not visible, make a reasonable inference or use placeholder
- Ensure age is a number, not a string
- Do NOT use trailing commas in arrays or objects
- Use double quotes for all strings, never single quotes
- Only extract what is actually visible in the prescription
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

    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize extraction service.

        Args:
            model: Gemini model to use for extraction
        """
        api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_CLOUD_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type from file extension."""
        ext = file_path.suffix.lower()
        mime_type = MIME_TYPES.get(ext)
        if not mime_type:
            raise ValueError(f"Unsupported file type: {ext}")
        return mime_type

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
        # 1. Load file bytes
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # 2. Get MIME type
        mime_type = self._get_mime_type(file_path)

        # 3. Call Gemini with image + prompt
        response = self.client.models.generate_content(
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
                temperature=0.1,  # Low for accuracy
                max_output_tokens=4096,
                response_mime_type="application/json",  # Force JSON output
            ),
        )

        # 4. Parse JSON response
        json_text = response.text.strip()

        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            # Remove first line (```json) and last line (```)
            json_text = "\n".join(lines[1:-1])

        # Try parsing, with repair fallback
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            # Try repairing common JSON issues
            repaired = _repair_json(json_text)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                # Log the raw response for debugging
                raise ValueError(
                    f"Failed to parse Gemini response as JSON: {e}\n"
                    f"Raw response (first 500 chars): {json_text[:500]}"
                ) from e

        # 5. Save to disk if path provided
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # 6. Return as Pydantic model
        return ExtractedOCRInput(**data)
