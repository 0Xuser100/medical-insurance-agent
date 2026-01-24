# Medical Insurance Automated Approval System

## Overview

An **Automated Claims & Pre-Authorization Engine** that processes prescription images to generate approval, rejection, or warning reports with Human-in-the-Loop review for doctors.

---

## 1. High-Level Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐
│  INGESTION  │───▶│    EXTRACTION    │───▶│ CONTEXT RETRIEVAL│───▶│  AI VALIDATION   │───▶│   OUTPUT    │
│             │    │  (GCP Doc AI)    │    │  (Patient Hx)*   │    │     AGENT        │    │   (JSON)    │
└─────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘    └─────────────┘
     │                    │                        │                       │                     │
  Upload            Extract:                 Query DB for           Run 3 Guardrails:      Structured
  Image/PDF         - Patient Name           last 30 days          - Clinical Match       JSON for
                    - Diagnosis (ICD-10)     of claims             - Medication Limit     Frontend UI
                    - Medications (Rx)       (* Not in MVP)        - Medication Duration
                    - Lab/Radiology
```

### Pipeline Steps

| Step | Component | Description |
|------|-----------|-------------|
| 1 | **Ingestion** | User uploads prescription image/PDF |
| 2 | **Extraction** | GCP Document AI / Healthcare NLP extracts entities |
| 3 | **Context Retrieval** | Query patient history (last 30 days) - *Not in MVP* |
| 4 | **AI Validation Agent** | Core brain - runs 3 guardrail checks |
| 5 | **Output** | Structured JSON for Frontend consumption |

---

## 2. GCP Extraction Strategy

### Does Document AI Have a Prescription Processor?

**No.** GCP Document AI does **NOT** have a dedicated prescription processor.

Available Document AI processors focus on:
- General OCR (Enterprise Document OCR)
- Financial documents (invoices, bank statements, W2)
- Identity documents (passports, driver's licenses)
- Custom extractors (requires training)

### Recommended Approach: Two-Step Pipeline

```
┌──────────────────┐      ┌─────────────────────────┐      ┌──────────────────┐
│  Prescription    │      │   Document AI           │      │  Healthcare NLP  │
│  Image/PDF       │─────▶│   (OCR → Raw Text)      │─────▶│  API (Entities)  │
└──────────────────┘      └─────────────────────────┘      └──────────────────┘
                                    │                               │
                               Raw text                    Structured output:
                               extraction                  - Medications
                                                          - Diagnoses (ICD)
                                                          - Procedures
                                                          - Dosages
```

### Step 1: Document AI (OCR)

Use **Enterprise Document OCR** or **Form Parser** to extract raw text from prescription images.

```python
# Document AI - Extract raw text
from google.cloud import documentai_v1 as documentai

def extract_text_from_prescription(image_bytes: bytes) -> str:
    client = documentai.DocumentProcessorServiceClient()

    # Use OCR processor
    raw_document = documentai.RawDocument(
        content=image_bytes,
        mime_type="image/jpeg"
    )

    request = documentai.ProcessRequest(
        name=processor_name,  # Your OCR processor
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    return result.document.text
```

### Step 2: Healthcare Natural Language API (Entity Extraction)

Pass the extracted text to **Healthcare NLP API** for medical entity recognition.

**What Healthcare NLP API Extracts:**

| Entity Type | Examples |
|-------------|----------|
| **Medications** | Azithromycin 500mg, Propranolol 40mg |
| **Diagnoses** | Acute Bronchitis, Hypertension |
| **Procedures** | Chest X-Ray, CT Scan |
| **Body Parts** | Lungs, Heart |
| **Dosages** | 500mg, twice daily |

**Key Features:**
- Auto-normalizes to **ICD-10**, **RxNorm**, **MeSH** codes
- Distinguishes past vs. current medications
- Identifies patient vs. family history context
- HIPAA compliant

```python
# Healthcare NLP API - Extract medical entities
from google.cloud import healthcare_v1

def extract_medical_entities(text: str) -> dict:
    client = healthcare_v1.HealthcareNaturalLanguageServiceClient()

    request = healthcare_v1.AnalyzeEntitiesRequest(
        nlp_service=nlp_service_name,
        document_content=text
    )

    response = client.analyze_entities(request=request)

    medications = []
    diagnoses = []

    for entity in response.entities:
        if entity.vocabulary_codes:  # Has standardized code
            if "RXNORM" in str(entity.vocabulary_codes):
                medications.append({
                    "name": entity.text,
                    "code": entity.vocabulary_codes,
                    "confidence": entity.confidence
                })
            elif "ICD10" in str(entity.vocabulary_codes):
                diagnoses.append({
                    "description": entity.text,
                    "icd_code": entity.vocabulary_codes,
                    "confidence": entity.confidence
                })

    return {"medications": medications, "diagnoses": diagnoses}
```

### Alternative: Custom Document AI Extractor

If Healthcare NLP API doesn't meet your needs, you can train a **Custom Extractor**:

1. Collect 50-100 labeled prescription samples
2. Define entity labels (medication_name, dosage, diagnosis, etc.)
3. Train custom processor in Document AI console
4. Deploy and use via API

**Pros:** Tailored to your prescription format
**Cons:** Requires labeled training data, ongoing maintenance

### API Comparison

| Feature | Document AI | Healthcare NLP API |
|---------|-------------|-------------------|
| **Input** | Images, PDFs | Text only |
| **Output** | Raw text, key-value pairs | Medical entities with codes |
| **Medical Codes** | No | Yes (ICD-10, RxNorm, MeSH) |
| **HIPAA** | Yes | Yes |
| **Custom Training** | Yes (Custom Extractor) | Yes (AutoML Entity Extraction) |
| **Best For** | OCR, form parsing | Medical text understanding |

### Recommendation for MVP

```
Prescription Image
       │
       ▼
┌─────────────────────┐
│ Document AI OCR     │  ← Step 1: Image to Text
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ Healthcare NLP API  │  ← Step 2: Text to Entities
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ Validation Agent    │  ← Step 3: Apply Guardrails
└─────────────────────┘
```

**Sources:**
- [Document AI Processors List](https://docs.cloud.google.com/document-ai/docs/processors-list)
- [Healthcare Natural Language API](https://cloud.google.com/blog/topics/healthcare-life-sciences/now-in-preview-healthcare-natural-language-api-and-automl-entity-extraction-for-healthcare)
- [Medical Entity Extraction Guide](https://medium.com/google-cloud/medical-entity-extraction-on-google-cloud-a-comprehensive-guide-898d7a5fc173)

---

## 3. AI Validation Agent - The Core Brain

The validation agent runs extracted data against **three guardrails**:

### Guardrail 1: Clinical Match Check

Validates that medications and labs align with the diagnosis.

```
┌─────────────────────────────────────────────────────────────────┐
│  CLINICAL MATCH CHECK                                           │
├─────────────────────────────────────────────────────────────────┤
│  Input:    Diagnosis: Acute Bronchitis (J20.9)                  │
│            Medication: Propranolol (Beta-blocker)               │
│            Lab: Chest X-Ray                                     │
│                                                                 │
│  Logic:    Is Propranolol valid for Acute Bronchitis?           │
│            Is Chest X-Ray valid for Acute Bronchitis?           │
│                                                                 │
│  Result:   Propranolol → NO  → FLAG (Not indicated)             │
│            Chest X-Ray → YES → PASS                             │
│                                                                 │
│  Data Source: diagnosis_mappings.json                           │
└─────────────────────────────────────────────────────────────────┘
```

### Guardrail 2: Medication Limit Check

Flags prescriptions with too many medications for doctor review.

```
┌─────────────────────────────────────────────────────────────────┐
│  MEDICATION LIMIT CHECK                                         │
├─────────────────────────────────────────────────────────────────┤
│  Input:    Prescription with 7 medications                      │
│  Rule:     More than 5 medications in single prescription?      │
│                                                                 │
│  Logic:    Count(medications) > 5                               │
│  Result:   YES → STATUS: Doctor Review Needed                   │
│            NO  → STATUS: Continue validation                    │
│                                                                 │
│  Rationale: Polypharmacy risk - drug interactions increase      │
│             exponentially with medication count                 │
└─────────────────────────────────────────────────────────────────┘
```

### Guardrail 3: Medication Duration Check

Ensures minimum time between same medication prescriptions.

```
┌─────────────────────────────────────────────────────────────────┐
│  MEDICATION DURATION CHECK                                      │
├─────────────────────────────────────────────────────────────────┤
│  Input:    Medication: Panadol Extra                            │
│            Last Dispensed: 10 days ago                          │
│                                                                 │
│  Rule:     Minimum 2 weeks (14 days) between prescriptions      │
│                                                                 │
│  Logic:    Days since last dispensed < 14?                      │
│  Result:   YES (10 < 14) → FLAG (Too soon to refill)            │
│            NO            → PASS                                 │
│                                                                 │
│  Data Source: Patient prescription history (database)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Final JSON Output Structure

This JSON drives the Frontend UI for "Patient Profile Card" and "AI Validation Engine" sections.

### Key Design Decisions

| Feature | Rationale |
|---------|-----------|
| **Line-item validation** | Each medication/procedure validated independently (partial approvals possible) |
| **`ui_badge` field** | Direct mapping to frontend badge components |
| **`risk_level`** | Visual prioritization (HIGH items surface first) |
| **Bilingual messages** | `reason_en` / `reason_ar` for Arabic-speaking markets |
| **`linked_history_id`** | Traceability to previous claims for audit |
| **`history_summary`** | Enables contraindication checks against patient conditions |

### Complete JSON Schema

```json
{
  "transaction_id": "REQ-2024-8859",
  "timestamp": "2024-05-21T10:30:00Z",

  "patient_profile": {
    "id": "PAT-10023",
    "name": "Ahmed Hassan",
    "age": 45,
    "gender": "Male",
    "insurance_tier": "Gold",
    "history_summary": "Chronic Hypertension, History of Asthma"
  },

  "extracted_context": {
    "primary_diagnosis": "Acute Bronchitis",
    "icd_code": "J20.9",
    "provider_id": "DR-5501"
  },

  "ai_validation_engine": {
    "overall_status": "REVIEW_NEEDED",
    "confidence_score": 0.98,
    "summary_message": "Request partially approved. One medication flagged for duplication. One medication has safety concerns.",

    "line_items": [
      {
        "type": "MEDICATION",
        "item_name": "Azithromycin 500mg",
        "status": "APPROVED",
        "ui_badge": "Auto-Approved",
        "risk_level": "LOW",
        "validation_details": {
          "clinical_match": true,
          "duration_check": "Passed (Last dispensed: 6 months ago)"
        }
      },
      {
        "type": "MEDICATION",
        "item_name": "Panadol Extra",
        "status": "FLAGGED",
        "ui_badge": "Rejected - Too Soon",
        "risk_level": "MEDIUM",
        "validation_details": {
          "clinical_match": true,
          "duration_check": "FAILED",
          "reason_en": "Patient received this medication 10 days ago. Minimum 2 weeks required.",
          "reason_ar": "المريض صرف هذا الدواء منذ 10 أيام. يجب الانتظار أسبوعين على الأقل",
          "linked_history_id": "CLAIM-9982"
        }
      },
      {
        "type": "MEDICATION",
        "item_name": "Propranolol",
        "status": "FLAGGED",
        "ui_badge": "Safety Alert",
        "risk_level": "HIGH",
        "validation_details": {
          "clinical_match": false,
          "reason_en": "Not indicated for Acute Bronchitis diagnosis.",
          "reason_ar": "الدواء غير مناسب لتشخيص التهاب الشعب الهوائية الحاد"
        }
      },
      {
        "type": "LAB_ANALYSIS",
        "item_name": "Chest CT Scan",
        "status": "APPROVED",
        "ui_badge": "Auto-Approved",
        "risk_level": "LOW",
        "validation_details": {
          "clinical_match": true,
          "duration_check": "N/A (Lab test)"
        }
      }
    ]
  }
}
```

---

## 5. Schema Analysis & Discussion Points

### Strengths of This Design

| Aspect | Why It Works |
|--------|--------------|
| **Line-item granularity** | Real prescriptions have multiple items; some pass, some fail. This allows partial approvals. |
| **UI-ready fields** | `ui_badge` and `risk_level` eliminate frontend transformation logic |
| **Bilingual support** | Essential for MENA region healthcare systems |
| **Audit traceability** | `linked_history_id` connects rejections to source claims |
| **Patient context** | `history_summary` enables the critical Propranolol/Asthma catch |

### Discussion Points

#### 1. Status Values - Are These Complete?

Current statuses:
- `APPROVED` - Auto-approved
- `FLAGGED` - Rejected or safety alert
- `PENDING_REVIEW` - Needs doctor decision

**Question:** Should `FLAGGED` be split into `REJECTED` vs `WARNING`?

```
FLAGGED (current) → Could mean:
  - Hard reject (Propranolol/Asthma - never approve)
  - Soft flag (Duplicate Panadol - doctor can override)
```

**Suggestion:** Add `rejection_type: "HARD" | "SOFT"` to `validation_details`?

---

#### 2. Missing Fields to Consider

| Field | Purpose | Add to MVP? |
|-------|---------|-------------|
| `medication_count` | Total medications in prescription | Yes |
| `requires_action_by` | Deadline for doctor review | Post-MVP |
| `alternative_suggestions` | Generic alternatives for rejected drugs | Post-MVP |

---

#### 3. Clinical Match - What Data Source?

The diagnosis-medication-labs matching requires a **mapping database**.

**MVP Approach:** Use a curated JSON file (`diagnosis_mappings.json`) that maps:
- ICD-10 codes → Valid medications
- ICD-10 codes → Recommended lab tests

Example:
```json
{
  "J20.9": {
    "name": "Acute Bronchitis",
    "valid_medications": ["Azithromycin", "Amoxicillin", "Dextromethorphan"],
    "valid_labs": ["Chest X-Ray", "CBC", "Sputum Culture"]
  }
}
```

---

#### 4. How Does `history_summary` Get Populated?

Current: `"Chronic Hypertension, History of Asthma"`

This implies the system needs:
1. Patient database with condition history
2. Or: Extract from previous claims
3. Or: Manual entry at patient registration

**Question:** For MVP, is this manually entered or pulled from an existing system?

---

## 6. Updated Pydantic Schemas

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class ItemType(str, Enum):
    MEDICATION = "MEDICATION"
    LAB_ANALYSIS = "LAB_ANALYSIS"
    RADIOLOGY = "RADIOLOGY"
    PROCEDURE = "PROCEDURE"

class ItemStatus(str, Enum):
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    PENDING_REVIEW = "PENDING_REVIEW"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class OverallStatus(str, Enum):
    APPROVED = "APPROVED"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    REJECTED = "REJECTED"

class ValidationDetails(BaseModel):
    clinical_match: bool
    duration_check: Optional[str] = None
    reason_en: Optional[str] = None
    reason_ar: Optional[str] = None
    linked_history_id: Optional[str] = None

class LineItem(BaseModel):
    type: ItemType
    item_name: str
    status: ItemStatus
    ui_badge: str
    risk_level: RiskLevel
    validation_details: ValidationDetails

class PatientProfile(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    insurance_tier: str
    history_summary: str

class ExtractedContext(BaseModel):
    primary_diagnosis: str
    icd_code: str
    provider_id: str

class AIValidationEngine(BaseModel):
    overall_status: OverallStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    summary_message: str
    line_items: list[LineItem]

class PrescriptionValidationResponse(BaseModel):
    transaction_id: str
    timestamp: datetime
    patient_profile: PatientProfile
    extracted_context: ExtractedContext
    ai_validation_engine: AIValidationEngine
```

---

## 7. Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | LangGraph | State management, conditional routing |
| **OCR/Extraction** | GCP Document AI | Healthcare NLP, entity extraction |
| **Clinical Validation** | Rules Engine + JSON Lookup | Diagnosis-medication matching |
| **Schema Validation** | Pydantic + Instructor | Structured LLM outputs |
| **LLM** | Claude | Reasoning, edge case handling |
| **Database** | PostgreSQL | Patient history, audit logs |
| **API** | FastAPI | REST endpoints |
| **Frontend** | React/Next.js | Doctor review UI |

---

## 8. Project Structure

```
medical-insurance-agent/
├── src/
│   ├── agents/
│   │   ├── extraction_agent.py      # GCP Document AI integration
│   │   ├── validation_agent.py      # Core validation logic
│   │   └── orchestrator.py          # LangGraph workflow
│   ├── models/
│   │   └── schemas.py               # Pydantic models (above)
│   ├── validators/
│   │   ├── clinical_match.py        # Guardrail 1: Clinical consistency
│   │   ├── medication_limit.py      # Guardrail 2: >5 medications = review
│   │   └── medication_duration.py   # Guardrail 3: 2-week minimum
│   ├── data/
│   │   └── diagnosis_mappings.json  # Diagnosis → valid medications/labs
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   └── routes/
│   │       ├── prescription.py      # Upload & process endpoints
│   │       └── review.py            # Doctor review endpoints
│   └── utils/
│       └── gcp_client.py            # GCP Document AI client
├── tests/
│   ├── test_clinical_match.py
│   ├── test_medication_limit.py
│   └── test_medication_duration.py
├── config/
│   └── settings.py                  # Environment config
├── requirements.txt
└── README.md
```

---

## 9. MVP Scope

### In Scope (MVP)
- [x] Prescription image upload
- [x] GCP Document AI extraction
- [x] Three guardrail validations
- [x] Line-item level validation
- [x] Bilingual messages (EN/AR)
- [x] Structured JSON output
- [x] Basic doctor review queue

### Out of Scope (Post-MVP)
- [ ] Patient history context retrieval (30-day lookback)
- [ ] Real-time insurance eligibility check
- [ ] Appeals workflow
- [ ] Alternative drug suggestions
- [ ] Mobile app

---

## 10. Open Questions for Discussion

1. **Should `FLAGGED` be split into `REJECTED` vs `WARNING`?**
2. **What is the data source for patient `history_summary`?**
3. **Should medication limit threshold be configurable?** (currently hardcoded at 5)
4. **Should duration threshold be configurable?** (currently hardcoded at 2 weeks)

---

## 11. Next Steps

1. **Finalize JSON schema** - Resolve discussion points above
2. **Set up GCP Document AI** - Configure Healthcare NLP processor
3. **Build diagnosis mappings** - Create `diagnosis_mappings.json` for clinical match
4. **Implement Pydantic schemas** - Define data contracts
5. **Build validation guardrails** - Three core checks:
   - Clinical Match (diagnosis ↔ medications/labs)
   - Medication Limit (>5 = doctor review)
   - Medication Duration (2-week minimum)
6. **Create LangGraph workflow** - Orchestrate pipeline
7. **Build FastAPI endpoints** - REST API
8. **Simple review UI** - Doctor approval interface


uv run uvicorn src.api.main:app --reload