# Medical Insurance Validation API

AI-powered prescription validation system that processes prescription images and generates approval/rejection reports with Human-in-the-Loop review.

---

## Quick Start

### Option 1: Local Development

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment (see Configuration section)
cp .env.example .env  # Edit with your API keys

# 3. Run server
uv run uvicorn src.api.main:app --reload
```

### Option 2: Docker

```bash
# Build image
docker build -t medical-insurance-api .

# Run container
docker run -p 8000:8000 --env-file .env medical-insurance-api
```

API available at: `http://localhost:8000/docs`

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UPLOAD    │────▶│   EXTRACT   │────▶│  VALIDATE   │────▶│   RESULT    │
│  Image/PDF  │     │ Gemini OCR  │     │  3 Rules    │     │    JSON     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Workflow

1. **Upload**: Client sends prescription image/PDF
2. **Extract**: Gemini Vision OCR extracts patient, diagnosis, medications
3. **Validate**: Three guardrails verify clinical correctness
4. **Result**: Structured JSON with line-item approvals/rejections

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload prescription file |
| POST | `/process` | Start OCR + validation |
| GET | `/result/{job_id}` | Get result (poll until COMPLETED) |
| GET | `/jobs` | List all jobs |
| DELETE | `/job/{job_id}` | Delete job |

### Example Flow

```bash
# 1. Upload
curl -X POST http://localhost:8000/upload -F "file=@prescription.jpg"
# Returns: {"job_id": "PAT-abc123..."}

# 2. Process
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"job_id": "PAT-abc123..."}'

# 3. Poll result
curl http://localhost:8000/result/PAT-abc123...
```

---

## Validation Guardrails

### 1. Clinical Match Check
Validates medications match the diagnosis using ICD-10 mappings.
```
Diagnosis: Acute Bronchitis (J20.9)
├── Azithromycin ──► APPROVED (valid for J20.9)
└── Propranolol  ──► FLAGGED (not indicated)
```

### 2. Medication Limit Check
Flags prescriptions with >5 medications for review.

### 3. Medication Duration Check
Ensures 14-day minimum between same medication refills.

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
│   │   ├── report_builder.py        # Builds JSON response
│   │   ├── job_store.py             # In-memory job storage
│   │   └── file_service.py          # File upload handling
│   ├── validators/
│   │   ├── clinical_match.py        # Guardrail 1
│   │   ├── medication_limit.py      # Guardrail 2
│   │   └── medication_duration.py   # Guardrail 3
│   ├── agents/
│   │   └── validation_crew.py       # CrewAI multi-agent
│   └── data/
│       └── diagnosis_mappings.json  # ICD-10 mappings
├── uploads/                         # Uploaded files
├── Dockerfile
├── .env
└── pyproject.toml
```

---

## Configuration

Create a `.env` file:

```env
# OpenAI (for CrewAI agent)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL_NAME="gpt-4o-mini"

# Google Cloud (for Gemini OCR)
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
GEMINI_MODEL_NAME="gemini-2.5-flash-preview-04-17"
GOOGLE_APPLICATION_CREDENTIALS="your-service-account.json"

# Validation rules
MEDICATION_LIMIT=5
MIN_DURATION_DAYS=14

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Job Status Flow

```
UPLOADED ──► EXTRACTING ──► VALIDATING ──► COMPLETED
                │                              │
                └──────────► FAILED ◄──────────┘
```

---

## Response Schema

```json
{
  "job_id": "PAT-abc123...",
  "status": "COMPLETED",
  "result": {
    "transaction_id": "REQ-2024-A1B2",
    "patient_profile": {
      "id": "PAT-10023",
      "name": "Ahmed Hassan",
      "age": 45
    },
    "ai_validation_engine": {
      "overall_status": "REVIEW_NEEDED",
      "confidence_score": 0.75,
      "line_items": [
        {
          "item_name": "Azithromycin 500mg",
          "status": "APPROVED",
          "risk_level": "LOW"
        }
      ]
    }
  }
}
```

---

## Client Integration (JavaScript)

```javascript
// 1. Upload
const { job_id } = await fetch('/upload', {
  method: 'POST',
  body: formData
}).then(r => r.json());

// 2. Process
await fetch('/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ job_id })
});

// 3. Poll result
let result;
while (true) {
  result = await fetch(`/result/${job_id}`).then(r => r.json());
  if (['COMPLETED', 'FAILED'].includes(result.status)) break;
  await new Promise(r => setTimeout(r, 1000));
}
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| OCR | Google Gemini Vision |
| Validation Agent | CrewAI + OpenAI |
| Schema | Pydantic |
| Package Manager | uv |