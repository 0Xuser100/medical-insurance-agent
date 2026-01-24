# Medical Insurance Validation API - End-to-End Documentation

## Overview

AI-powered prescription validation system that processes prescription images and generates approval/rejection reports.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UPLOAD    │────▶│   EXTRACT   │────▶│  VALIDATE   │────▶│   RESULT    │
│  Image/PDF  │     │ Gemini OCR  │     │  3 Rules    │     │    JSON     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Create `.env` file:

```env
# OpenAI (for CrewAI agent)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL_NAME="gpt-4o-mini"

# Google Cloud (for Gemini OCR)
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
GEMINI_MODEL_NAME="gemini-2.5-flash-preview-04-17"
GOOGLE_APPLICATION_CREDENTIALS="your-service-account.json"

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Run Server

```bash
uv run uvicorn src.api.main:app --reload
```

---

## API Endpoints

### Upload File

```
POST /upload
Content-Type: multipart/form-data
```

Upload a prescription image or PDF.

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@prescription.jpg"
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "UPLOADED",
  "filename": "prescription.jpg",
  "file_size": 245678,
  "created_at": "2024-01-15T10:30:00Z",
  "message": "File uploaded. Call POST /process to start."
}
```

---

### Start Processing

```
POST /process
Content-Type: application/json
```

Start OCR extraction and validation.

**Request:**
```json
{
  "job_id": "job-abc123def456"
}
```

**Response:**
```json
{
  "job_id": "job-abc123def456",
  "status": "PROCESSING",
  "message": "Processing started. Poll GET /result/{job_id}"
}
```

---

### Get Result (Polling)

```
GET /result/{job_id}
```

Check job status. Poll until `COMPLETED` or `FAILED`.

**Response (Processing):**
```json
{
  "job_id": "job-abc123def456",
  "status": "EXTRACTING",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": null,
  "error": null,
  "extracted_data": null,
  "result": null
}
```

**Response (Completed):**
```json
{
  "job_id": "job-abc123def456",
  "status": "COMPLETED",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": "2024-01-15T10:30:12Z",
  "error": null,
  "extracted_data": {
    "patient_id": "PAT-10023",
    "patient_name": "Ahmed Hassan",
    "age": 45,
    "gender": "Male",
    "diagnosis": "Acute Bronchitis",
    "icd_code": "J20.9",
    "provider_id": "DR-5501",
    "medications": ["Azithromycin 500mg", "Panadol Extra"],
    "labs": ["Chest X-Ray"],
    "medication_history": {"Panadol Extra": 10},
    "insurance_tier": "Gold"
  },
  "result": {
    "transaction_id": "REQ-2024-A1B2",
    "timestamp": "2024-01-15T10:30:12Z",
    "patient_profile": {...},
    "extracted_context": {...},
    "ai_validation_engine": {
      "overall_status": "REVIEW_NEEDED",
      "confidence_score": 0.75,
      "summary_message": "1 of 2 medications flagged for review",
      "medication_count": 2,
      "line_items": [...]
    }
  }
}
```

---

### List Jobs

```
GET /jobs
GET /jobs?status=COMPLETED
```

List all jobs with optional status filter.

---

### Delete Job

```
DELETE /job/{job_id}
```

Delete a job and its files.

---

## Processing Pipeline

### Stage 1: Upload

```
Client ──► POST /upload ──► Save file to /uploads/{job_id}_{filename}
                         ──► Create job in memory store
                         ──► Return job_id
```

### Stage 2: Extraction (Gemini OCR)

```
POST /process ──► Load image/PDF bytes
              ──► Send to Gemini with extraction prompt
              ──► Parse JSON response
              ──► Save to /uploads/{job_id}_extracted.json
              ──► Return ExtractedOCRInput
```

**Extracted Fields:**
| Field | Description |
|-------|-------------|
| patient_id | Patient identifier |
| patient_name | Full name |
| age | Patient age |
| gender | Male/Female |
| diagnosis | Primary diagnosis |
| icd_code | ICD-10 code |
| provider_id | Doctor ID |
| medications | List of medications |
| labs | List of lab tests |
| medication_history | Previous dispensing data |

### Stage 3: Validation (3 Guardrails)

```
ExtractedOCRInput ──► Clinical Match Validator
                  ──► Medication Limit Validator
                  ──► Medication Duration Validator
                  ──► Merge results
                  ──► Build report
```

#### Guardrail 1: Clinical Match Check

Validates medications/labs match the diagnosis using ICD-10 mappings.

```
Diagnosis: Acute Bronchitis (J20.9)
├── Azithromycin 500mg ──► APPROVED (matches J20.9)
├── Propranolol ──► FLAGGED (not related to bronchitis)
└── Chest X-Ray ──► APPROVED (matches J20.9)
```

#### Guardrail 2: Medication Limit Check

Flags prescriptions with >5 medications for doctor review.

```
Medications: 6
├── Limit: 5
└── Status: PENDING_REVIEW (exceeds limit)
```

#### Guardrail 3: Medication Duration Check

Ensures minimum 14 days between same medication refills.

```
Panadol Extra
├── Last dispensed: 10 days ago
├── Minimum required: 14 days
└── Status: FLAGGED (too soon)
```

### Stage 4: Report Generation

```json
{
  "transaction_id": "REQ-2024-A1B2",
  "patient_profile": {
    "id": "PAT-10023",
    "name": "Ahmed Hassan"
  },
  "ai_validation_engine": {
    "overall_status": "REVIEW_NEEDED",
    "confidence_score": 0.75,
    "line_items": [
      {
        "type": "MEDICATION",
        "item_name": "Azithromycin 500mg",
        "status": "APPROVED",
        "risk_level": "LOW",
        "validation_details": {
          "clinical_match": true,
          "reason_en": "Matches diagnosis"
        }
      },
      {
        "type": "MEDICATION",
        "item_name": "Panadol Extra",
        "status": "FLAGGED",
        "risk_level": "MEDIUM",
        "validation_details": {
          "clinical_match": true,
          "duration_check": "FAILED",
          "reason_en": "Dispensed 10 days ago, minimum 14 days required",
          "reason_ar": "تم صرفه قبل 10 أيام، الحد الأدنى المطلوب 14 يوماً"
        }
      }
    ]
  }
}
```

---

## Job Status Flow

```
UPLOADED ──► EXTRACTING ──► VALIDATING ──► COMPLETED
                │                              │
                └──────────► FAILED ◄──────────┘
```

| Status | Description |
|--------|-------------|
| UPLOADED | File received, waiting for /process |
| EXTRACTING | Gemini OCR in progress |
| VALIDATING | Running 3 guardrails |
| COMPLETED | Done, result available |
| FAILED | Error occurred, check error field |

---

## Project Structure

```
medical-insurance-agent/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI endpoints
│   │   └── dependencies.py      # Dependency injection
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── services/
│   │   ├── extraction_service.py    # Gemini OCR
│   │   ├── processing_service.py    # Background jobs
│   │   ├── validation_service.py    # Orchestrates validators
│   │   ├── report_builder.py        # Builds JSON response
│   │   ├── job_store.py             # In-memory job storage
│   │   └── file_service.py          # File upload handling
│   ├── validators/
│   │   ├── base.py                  # Base validator class
│   │   ├── clinical_match.py        # Guardrail 1
│   │   ├── medication_limit.py      # Guardrail 2
│   │   └── medication_duration.py   # Guardrail 3
│   ├── agents/
│   │   └── validation_crew.py       # CrewAI agent
│   ├── core/
│   │   └── protocols.py             # Abstract interfaces
│   └── data/
│       └── diagnosis_mappings.json  # ICD-10 → medications/labs
├── uploads/                         # Uploaded files (gitignored)
├── .env                             # Environment config
└── pyproject.toml                   # uv project config
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | - | OpenAI API key for CrewAI |
| OPENAI_MODEL_NAME | gpt-4o-mini | LLM model |
| GOOGLE_CLOUD_PROJECT | - | GCP project ID |
| GOOGLE_CLOUD_LOCATION | us-central1 | GCP region |
| GEMINI_MODEL_NAME | gemini-2.0-flash | Gemini model for OCR |
| GOOGLE_APPLICATION_CREDENTIALS | - | Service account JSON path |
| MEDICATION_LIMIT | 5 | Max medications before review |
| MIN_DURATION_DAYS | 14 | Min days between refills |
| API_HOST | 0.0.0.0 | Server host |
| API_PORT | 8000 | Server port |

---

## Client Integration Example

```javascript
// 1. Upload file
const uploadRes = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData  // FormData with 'file' field
});
const { job_id } = await uploadRes.json();

// 2. Start processing
await fetch('http://localhost:8000/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ job_id })
});

// 3. Poll for result
let result;
while (true) {
  const res = await fetch(`http://localhost:8000/result/${job_id}`);
  result = await res.json();

  if (result.status === 'COMPLETED' || result.status === 'FAILED') {
    break;
  }
  await new Promise(r => setTimeout(r, 1000)); // Wait 1s
}

// 4. Use result
console.log(result.result.ai_validation_engine.overall_status);
```

---

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S** - Single Responsibility | Each validator handles ONE guardrail |
| **O** - Open/Closed | Add validators without modifying existing code |
| **L** - Liskov Substitution | All validators implement ValidatorProtocol |
| **I** - Interface Segregation | Separate protocols for validators, report builder |
| **D** - Dependency Inversion | Services injected via constructor |
