"""
LLM Aggregator Prompt Engineering.

This module contains the prompt template for the final LLM aggregator
that synthesizes all agent responses into the structured schema.

Usage:
    from src.prompts.aggregator_prompt import build_aggregation_prompt
    prompt = build_aggregation_prompt(ocr_data, agent_results)
"""

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a Medical Insurance Validation Response Aggregator.

Your role is to synthesize raw OCR extraction data and validation agent results 
into a structured JSON response format for a medical insurance validation system.

## Critical Rules:
1. Return ONLY valid JSON - no markdown, no explanations, no code blocks
2. Use the EXACT field names and structure specified in the schema
3. All enum values must be UPPERCASE (APPROVED, FLAGGED, PENDING_REVIEW, etc.)
4. confidence_score must be between 0.0 and 1.0
5. Generate bilingual reasons (English and Arabic) for flagged items
6. Be conservative - when uncertain, use PENDING_REVIEW status
"""

# =============================================================================
# MAIN AGGREGATION PROMPT
# =============================================================================

AGGREGATION_PROMPT_TEMPLATE = """
## Task
Analyze the provided OCR extraction data and plain text agent validation findings.
Synthesize all information into a single structured JSON response.

---

## Input Data

### 1. OCR Extracted Data (from prescription image):
```json
{ocr_data}
```

### 2. Agent Validation Findings (plain text):
```
{agent_text}
```

---

## Required Output Schema

You MUST return a JSON object with this EXACT structure:

```json
{{
  "transaction_id": "REQ-{year}-XXXX",
  "timestamp": "{timestamp}",
  "patient_profile": {{
    "id": "PAT-XXXXX",
    "name": "Patient Name",
    "age": 0,
    "gender": "Male",
    "insurance_tier": "Unknown",
    "history_summary": ""
  }},
  "extracted_context": {{
    "primary_diagnosis": "Diagnosis from prescription",
    "icd_code": "UNKNOWN",
    "provider_id": "DR-XXXX"
  }},
  "ai_validation_engine": {{
    "overall_status": "REVIEW_NEEDED",
    "confidence_score": 0.85,
    "summary_message": "Clear summary for display",
    "medication_count": 0,
    "line_items": [
      {{
        "type": "MEDICATION",
        "item_name": "Name of item",
        "status": "APPROVED",
        "ui_badge": "✓ Approved",
        "risk_level": "LOW",
        "validation_details": {{
          "clinical_match": true,
          "duration_check": "OK",
          "reason_en": "English reason for status",
          "reason_ar": "سبب بالعربية",
          "linked_history_id": null
        }}
      }}
    ]
  }}
}}
```

### Field Value Options:
- **gender**: "Male" or "Female"
- **insurance_tier**: "Gold", "Silver", "Bronze", or "Unknown"
- **icd_code**: Valid ICD-10 code string, or "UNKNOWN" if not available
- **overall_status**: "APPROVED", "REVIEW_NEEDED", or "REJECTED"
- **confidence_score**: Decimal number between 0.0 and 1.0
- **type**: "MEDICATION", "LAB_ANALYSIS", "RADIOLOGY", or "PROCEDURE"
- **status**: "APPROVED", "FLAGGED", or "PENDING_REVIEW"
- **ui_badge**: "✓ Approved", "⚠️ Review Needed", or "⏳ Pending"
- **risk_level**: "LOW", "MEDIUM", or "HIGH"
- **clinical_match**: boolean (true or false)
- **duration_check**: "OK", "Exceeds standard", or null (JSON null, not string)
- **linked_history_id**: String like "CLM-XXXX" or null (JSON null, not string)

---

## Agent Text Format

The agent validation findings use a plain text format with the following patterns:

- **CLINICAL CHECK - [medication]: APPROVED/FLAGGED.** - Clinical match validation
- **MEDICATION LIMIT CHECK: PASSED/PENDING_REVIEW.** - Policy limit check
- **DURATION CHECK - [medication]: PASSED.** - Refill interval check

Parse these to determine:
- Which medications were checked
- Their status (APPROVED, FLAGGED, PENDING_REVIEW)
- Risk level (mentioned as "Risk: HIGH/MEDIUM/LOW")
- Reasons for flagging (if any)

---

## Field Mapping Rules

### Patient Profile:
- Extract patient name, age, gender from OCR data if available
- Generate a unique patient ID in format "PAT-XXXXX" if not provided
- Default insurance_tier to "Unknown" if not specified
- Summarize any medical history mentioned, or leave empty

### Extracted Context:
- Extract primary diagnosis from prescription/OCR data
- Map to ICD-10 code if recognizable, otherwise use "UNKNOWN"
- Extract provider/doctor ID from prescription

### Validation Engine:
- **overall_status**: 
  - "APPROVED" if ALL items are APPROVED
  - "REVIEW_NEEDED" if ANY item is FLAGGED or PENDING_REVIEW
  - "REJECTED" if critical safety issues found

- **confidence_score**: Calculate as (approved_items / total_items)

- **summary_message**: Generate a clear, professional summary like:
  - "All items validated and approved for processing."
  - "3 of 5 items require clinical review before approval."
  - "Request flagged for compliance review due to [reason]."

### Line Items:
For each medication/procedure from OCR and agent results:

- **ui_badge** mappings:
  - APPROVED → "✓ Approved"
  - FLAGGED → "⚠️ Review Needed"  
  - PENDING_REVIEW → "⏳ Pending"

- **reason_en / reason_ar**: Always provide bilingual explanations:
  - For APPROVED: "Matches clinical guidelines" / "يتوافق مع الإرشادات السريرية"
  - For FLAGGED: Specific reason in both languages
  - For PENDING_REVIEW: "Awaiting additional verification" / "في انتظار التحقق الإضافي"

- **duration_check**: Evaluate prescription duration:
  - "OK" if within standard limits
  - "Exceeds standard 14-day limit" if too long
  - null if not applicable

---

## Examples of Bilingual Reasons

| Scenario | English | Arabic |
|----------|---------|--------|
| Approved | "Clinically appropriate for diagnosis" | "مناسب سريرياً للتشخيص" |
| Duplicate | "Duplicate prescription detected within 30 days" | "تم اكتشاف وصفة مكررة خلال 30 يوماً" |
| Dosage issue | "Dosage exceeds standard guidelines" | "الجرعة تتجاوز الإرشادات القياسية" |
| Not covered | "Medication not covered under current plan" | "الدواء غير مشمول في الخطة الحالية" |
| Duration | "Treatment duration exceeds policy limits" | "مدة العلاج تتجاوز حدود الوثيقة" |
| Clinical mismatch | "Does not match primary diagnosis" | "لا يتطابق مع التشخيص الرئيسي" |

---

## Important Notes

1. If OCR data is incomplete, use "UNKNOWN" or appropriate defaults
2. Count ONLY MEDICATION type items for medication_count
3. Generate transaction_id using current year and random 4 chars
4. Ensure all arrays are valid (empty array [] if no items)
5. All string fields must be non-null (use empty string "" if needed)

Now process the input data and return the structured JSON response.
"""


def build_aggregation_prompt(
    ocr_data: dict,
    agent_text: str,
    year: str = "2026",
    timestamp: str = ""
) -> str:
    """
    Build the complete aggregation prompt with input data.

    Args:
        ocr_data: Extracted OCR data from prescription image
        agent_text: Plain text validation findings from agents
        year: Current year for transaction ID
        timestamp: ISO timestamp string (generated if empty)

    Returns:
        Complete prompt string ready for LLM
    """
    import json
    from datetime import datetime

    if not timestamp:
        timestamp = datetime.now().isoformat()

    return AGGREGATION_PROMPT_TEMPLATE.format(
        ocr_data=json.dumps(ocr_data, indent=2, ensure_ascii=False),
        agent_text=agent_text if agent_text else "No agent validation results available.",
        year=year,
        timestamp=timestamp
    )


# =============================================================================
# CONFIGURATION FOR GEMINI
# =============================================================================

AGGREGATOR_CONFIG = {
    "temperature": 0.1,  # Low temp for consistent structured output
    "response_mime_type": "application/json",  # Force JSON response
    "max_output_tokens": 4096,  # Sufficient for full response
}
