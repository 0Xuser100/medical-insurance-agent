# LLM Aggregator Layer Implementation

This document describes the changes made to add an LLM aggregator layer to the Medical Insurance Validation system. The aggregator uses Gemini to synthesize OCR extraction data and agent validation results into a structured final response.

## Overview

The system now follows a 4-stage pipeline:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  EXTRACTION  │────▶│  VALIDATION  │────▶│  AGGREGATION │────▶│    OUTPUT    │
│  (Gemini     │     │  (CrewAI     │     │  (Gemini     │     │  (Structured │
│   OCR)       │     │   Agents)    │     │   LLM)       │     │   JSON)      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Changes

1. **New LLM Aggregator Service** - Synthesizes final response using Gemini
2. **Bilingual Output** - Proper Arabic/English reasons for all items
3. **Proper UI Badges** - "✓ Approved", "⚠️ Review Needed", "⏳ Pending"
4. **Complete Response Schema** - Includes `extracted_context` with diagnosis/ICD/provider

## Files Changed

### New Files

| File | Description |
|------|-------------|
| `src/services/llm_aggregator_service.py` | LLM aggregator using Gemini API |
| `src/prompts/aggregator_prompt.py` | Prompt template for aggregation |
| `src/prompts/__init__.py` | Package exports |

### Modified Files

| File | Changes |
|------|---------|
| `src/agents/validation_crew.py` | Added `llm_aggregator` dependency, uses it for final synthesis |
| `src/api/dependencies.py` | Added `get_llm_aggregator()` factory function |
| `src/api/main.py` | Added `AGGREGATING` status handling |
| `src/models/schemas.py` | Added `AGGREGATING` to `JobStatus` enum |
| `src/services/job_store.py` | Added `mark_aggregating()` method to `Job` class |

## Architecture

### Processing Flow

```
POST /upload → File saved → Job created (UPLOADED)
                              ↓
POST /process → Background task started
                              ↓
Phase 1: EXTRACTING → Gemini OCR extracts data from image
                              ↓
Phase 2: VALIDATING → CrewAI agents run validation checks
    - Clinical Pharmacist: Drug-diagnosis matching
    - Compliance Officer: Medication limit check
    - History Analyst: Duration/refill check
                              ↓
Phase 3: AGGREGATING → Gemini LLM synthesizes final response
    - Combines OCR data + validation results
    - Generates bilingual reasons (EN/AR)
    - Creates proper UI badges
    - Fills in extracted_context
                              ↓
COMPLETED → Final JSON response available
```

### Dependency Injection

```python
# src/api/dependencies.py

@lru_cache
def get_llm_aggregator() -> LLMAggregatorService:
    return LLMAggregatorService()

@lru_cache
def get_validation_crew() -> ValidationCrew:
    return ValidationCrew(
        report_builder=get_report_builder(),
        llm_aggregator=get_llm_aggregator(),  # NEW
    )
```

## Output Schema Improvements

### Before (ReportBuilder)

```json
{
  "ui_badge": "Auto-Approved",
  "validation_details": {
    "reason_en": null,
    "reason_ar": null
  }
}
```

### After (LLM Aggregator)

```json
{
  "ui_badge": "✓ Approved",
  "validation_details": {
    "reason_en": "Clinically appropriate for diagnosis",
    "reason_ar": "مناسب سريرياً للتشخيص"
  }
}
```

### Complete Response Structure

```json
{
  "transaction_id": "REQ-2026-XXXX",
  "timestamp": "2026-01-25T10:18:58.813441",
  "patient_profile": {
    "id": "PAT-edce340e42b8",
    "name": "Omar Mohamed Hatem",
    "age": 6,
    "gender": "Male",
    "insurance_tier": "Unknown",
    "history_summary": ""
  },
  "extracted_context": {
    "primary_diagnosis": "Respiratory condition",
    "icd_code": "J06.9",
    "provider_id": "DR-WaelHatem"
  },
  "ai_validation_engine": {
    "overall_status": "APPROVED",
    "confidence_score": 1.0,
    "summary_message": "All items validated and approved for processing.",
    "medication_count": 3,
    "line_items": [
      {
        "type": "MEDICATION",
        "item_name": "Azulast phys N. spray",
        "status": "APPROVED",
        "ui_badge": "✓ Approved",
        "risk_level": "LOW",
        "validation_details": {
          "clinical_match": true,
          "duration_check": "OK",
          "reason_en": "Clinically appropriate for diagnosis",
          "reason_ar": "مناسب سريرياً للتشخيص",
          "linked_history_id": null
        }
      }
    ]
  }
}
```

## UI Badge Mappings

| Status | Badge |
|--------|-------|
| APPROVED | ✓ Approved |
| FLAGGED | ⚠️ Review Needed |
| PENDING_REVIEW | ⏳ Pending |

## Bilingual Reason Examples

| Scenario | English | Arabic |
|----------|---------|--------|
| Approved | "Clinically appropriate for diagnosis" | "مناسب سريرياً للتشخيص" |
| Duplicate | "Duplicate prescription detected within 30 days" | "تم اكتشاف وصفة مكررة خلال 30 يوماً" |
| Dosage issue | "Dosage exceeds standard guidelines" | "الجرعة تتجاوز الإرشادات القياسية" |
| Not covered | "Medication not covered under current plan" | "الدواء غير مشمول في الخطة الحالية" |
| Duration | "Treatment duration exceeds policy limits" | "مدة العلاج تتجاوز حدود الوثيقة" |
| Clinical mismatch | "Does not match primary diagnosis" | "لا يتطابق مع التشخيص الرئيسي" |

## Environment Variables

Add the following to your `.env` file:

```bash
# Gemini API (for OCR and Aggregation)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_NAME=gemini-3-flash-preview  # Optional, default: gemini-3-flash-preview

# OpenAI (for CrewAI agents)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_NAME=gpt-4o-mini  # Optional, default: gpt-4o-mini
```

## Aggregator Configuration

The LLM aggregator uses the following Gemini settings:

```python
AGGREGATOR_CONFIG = {
    "temperature": 0.1,  # Low temp for consistent structured output
    "response_mime_type": "application/json",  # Force JSON response
    "max_output_tokens": 4096,  # Sufficient for full response
}
```

## Fallback Behavior

If the LLM aggregator fails or is not configured, the system falls back to the original `ReportBuilder` for response generation:

```python
# In ValidationCrew.validate_prescription()
if self.llm_aggregator:
    return await self.llm_aggregator.aggregate(...)
else:
    return await self.report_builder.build_report(...)
```

## Testing

To test the aggregator:

```bash
# Run with aggregator (default)
uv run uvicorn src.api.main:app --reload

# Upload and process a prescription
curl -X POST http://localhost:8000/upload -F "file=@prescription.jpg"
curl -X POST http://localhost:8000/process -d '{"job_id": "PAT-xxxx"}'
curl http://localhost:8000/result/PAT-xxxx
```

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S** - Single Responsibility | LLMAggregatorService only handles aggregation |
| **O** - Open/Closed | Add new aggregators without modifying existing code |
| **L** - Liskov Substitution | Aggregator can be swapped with ReportBuilder |
| **I** - Interface Segregation | Minimal interface for aggregation |
| **D** - Dependency Inversion | Injected via constructor, not hard-coded |

## Complete API Response Example

Here's the full response format from `GET /result/{job_id}`:

```json
{
  "job_id": "PAT-edce340e42b8",
  "status": "COMPLETED",
  "created_at": "2026-01-25T10:15:26.166367",
  "started_at": "2026-01-25T10:15:50.474445",
  "completed_at": "2026-01-25T10:18:58.813960",
  "error": null,
  "extracted_data": {
    "doctor_information": {
      "name": "Dr. Wael Hatem El Taei",
      "specialization": "Consultant Pediatrician and Neonatologist",
      "qualifications": "PhD in Childhood Studies, Ain Shams University"
    },
    "patient_information": {
      "name": "Omar Mohamed Hatem",
      "date": "4/1/2024",
      "age": "6.5 years",
      "weight": "20.4 kg",
      "height": "121 cm"
    },
    "medications": [
      {
        "name": "Azulast phys N. spray",
        "dosage": "One puff in each nostril twice daily",
        "duration": "One month"
      },
      {
        "name": "Lelipel syrup",
        "dosage": "5 ml in the evening",
        "duration": "One month"
      },
      {
        "type": "Home Nebulizer",
        "components": ["Chicks saline", "Loxyine"],
        "dosage": "10 ml saline + 5 drops of medicine twice daily",
        "duration": "One week"
      }
    ],
    "clinic_details": {
      "consultation_policy": "Consultation within one week of examination",
      "phone_numbers": ["01008895351", "01063703736"],
      "facebook_page": "Dr Wael Hatem El Taei Clinic"
    }
  },
  "result": {
    "transaction_id": "REQ-2026-5DD7",
    "timestamp": "2026-01-25T10:18:58.813441",
    "patient_profile": {
      "id": "PAT-edce340e42b8",
      "name": "Omar Mohamed Hatem",
      "age": 6,
      "gender": "Male",
      "insurance_tier": "Unknown",
      "history_summary": ""
    },
    "extracted_context": {
      "primary_diagnosis": "Respiratory condition",
      "icd_code": "J06.9",
      "provider_id": "DR-WaelHatem"
    },
    "ai_validation_engine": {
      "overall_status": "APPROVED",
      "confidence_score": 1.0,
      "summary_message": "All items validated and approved for processing.",
      "medication_count": 3,
      "line_items": [
        {
          "type": "MEDICATION",
          "item_name": "Azulast phys N. spray",
          "status": "APPROVED",
          "ui_badge": "✓ Approved",
          "risk_level": "LOW",
          "validation_details": {
            "clinical_match": true,
            "duration_check": "OK",
            "reason_en": "Clinically appropriate for diagnosis",
            "reason_ar": "مناسب سريرياً للتشخيص",
            "linked_history_id": null
          }
        },
        {
          "type": "MEDICATION",
          "item_name": "Lelipel syrup",
          "status": "APPROVED",
          "ui_badge": "✓ Approved",
          "risk_level": "LOW",
          "validation_details": {
            "clinical_match": true,
            "duration_check": "OK",
            "reason_en": "Clinically appropriate for diagnosis",
            "reason_ar": "مناسب سريرياً للتشخيص",
            "linked_history_id": null
          }
        },
        {
          "type": "MEDICATION",
          "item_name": "Chicks saline",
          "status": "APPROVED",
          "ui_badge": "✓ Approved",
          "risk_level": "LOW",
          "validation_details": {
            "clinical_match": true,
            "duration_check": "OK",
            "reason_en": "Clinically appropriate for diagnosis",
            "reason_ar": "مناسب سريرياً للتشخيص",
            "linked_history_id": null
          }
        },
        {
          "type": "MEDICATION",
          "item_name": "Loxyine",
          "status": "APPROVED",
          "ui_badge": "✓ Approved",
          "risk_level": "LOW",
          "validation_details": {
            "clinical_match": true,
            "duration_check": "OK",
            "reason_en": "Clinically appropriate for diagnosis",
            "reason_ar": "مناسب سريرياً للتشخيص",
            "linked_history_id": null
          }
        }
      ]
    }
  }
}
```

## Future Improvements

1. **Caching** - Cache LLM responses for identical inputs
2. **Retry Logic** - Automatic retry on Gemini API failures
3. **Streaming** - Stream aggregation progress to client
4. **A/B Testing** - Compare aggregator vs report builder output
5. **Custom Prompts** - Per-client prompt customization
