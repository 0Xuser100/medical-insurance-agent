# Medical Insurance Validation API

AI-powered prescription validation system that processes prescription images/PDFs and generates structured approval/rejection reports with bilingual reasons (EN/AR) and Human-in-the-Loop review.

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
# 1. Configure environment
cp .env.example .env  # Edit with your API keys

# 2. Build and run
docker compose up --build

# 3. Stop
docker compose down
```

**After changing source code**, rebuild and restart:

```bash
docker compose up --build
```

API available at: `http://localhost:8000/docs`

### Deploy to Docker Hub

Replace `0x1000` with your actual Docker Hub username.

```bash
# 1. Build and run locally
docker compose up --build

# 2. Tag the image for Docker Hub
docker tag medical-insurance-agent-api 0x1000/medical-insurance-api:latest

# 3. Log in to Docker Hub
docker login

# 4. Push
docker push 0x1000/medical-insurance-api:latest
```

### Run on a Server

```bash
# 1. Pull the image
docker pull 0x1000/medical-insurance-api:latest

# 2. Run the container
docker run -d -p 8000:8000 --env-file .env 0x1000/medical-insurance-api:latest
```

---

## Architecture

The system uses a **LangChain + Gemini** pipeline that replaces the previous CrewAI multi-agent approach with a single unified LLM call using Gemini's native structured output.

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   UPLOAD    │────▶│   EXTRACT   │────▶│    VALIDATE      │────▶│   RESULT    │
│  Image/PDF  │     │ Gemini OCR  │     │ LangChain+Gemini │     │    JSON     │
│             │     │ (GenAI SDK) │     │ Structured Output│     │ (Bilingual) │
└─────────────┘     └─────────────┘     └──────────────────┘     └─────────────┘
```

### Processing Pipeline

1. **Upload** - Client sends a prescription image (JPEG, PNG, GIF, WebP, TIFF) or PDF (max 10MB)
2. **Extract** - Gemini Vision OCR extracts patient info, diagnosis, medications, labs, and provider details using structured JSON schema enforcement
3. **Validate** - LangChain invokes Gemini with native structured output to apply all 3 validation rules in a single call:
   - Clinical Match Check (ICD-10 medication-diagnosis matching)
   - Medication Limit Check (>5 medications triggers review)
   - Duration Check (refill interval validation, placeholder for MVP)
4. **Result** - Structured JSON with line-item approvals/rejections, bilingual reasons (EN/AR), and UI badges

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check / API info |
| POST | `/upload` | Upload prescription image/PDF |
| POST | `/process` | Start async OCR + validation |
| GET | `/result/{job_id}` | Poll for processing result |
| DELETE | `/job/{job_id}` | Cancel/delete a job |
| GET | `/jobs` | List all jobs (with optional `?status=` filter) |

### Example Flow

```bash
# 1. Upload
curl -X POST http://localhost:8000/upload -F "file=@prescription.jpg"
# Returns: {"job_id": "PAT-abc123...", "status": "UPLOADED", ...}

# 2. Process
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"job_id": "PAT-abc123..."}'
# Returns: {"job_id": "PAT-abc123...", "status": "PROCESSING", ...}

# 3. Poll result
curl http://localhost:8000/result/PAT-abc123...
# Returns full result when status is COMPLETED
```

---

## Validation Rules

All three rules are executed in a **single LLM call** via LangChain with Gemini's native structured output (schema enforced at token generation level).

### 1. Clinical Match Check
Validates each medication against the diagnosis using ICD-10 mappings with fuzzy matching (ignores dosage/form suffixes).
```
Diagnosis: Acute Bronchitis (J20.9)
├── Azithromycin 500mg ──► APPROVED (matches "Azithromycin" in J20.9 valid list)
└── Propranolol 40mg   ──► FLAGGED  (not in J20.9 valid medications)
```

### 2. Medication Limit Check
Flags the overall prescription for review when medication count exceeds the configured limit (default: 5). Individual medication statuses are not affected.

### 3. Duration Check
Validates refill intervals (minimum 14 days between same medication). Currently returns "OK" for all items in MVP (placeholder for patient history integration).

---

## Project Structure

```
medical-insurance-agent/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI app with 6 endpoints
│   │   └── dependencies.py                 # Dependency injection (SOLID - D)
│   ├── core/
│   │   ├── __init__.py
│   │   └── protocols.py                    # ValidationServiceProtocol interface
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                      # Pydantic models (enums, request/response)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extraction_service.py           # Gemini OCR extraction (Google GenAI SDK)
│   │   ├── langchain_validation_service.py # Unified validation (LangChain + Gemini)
│   │   ├── processing_service.py           # Background job orchestration
│   │   ├── job_store.py                    # In-memory job storage (async-safe)
│   │   └── file_service.py                 # File upload validation & storage
│   ├── prompts/
│   │   ├── __init__.py                     # Exports UNIFIED_VALIDATION_PROMPT
│   │   └── aggregator_prompt.py            # Unified validation prompt template
│   └── data/
│       └── diagnosis_mappings.json         # ICD-10 → valid medications/labs
├── tests/
│   ├── __init__.py
│   ├── test_api_schema.py                  # API endpoint schema tests
│   └── test_validators.py                  # Validator tests
├── uploads/                                # Uploaded files (runtime)
├── Dockerfile                              # Multi-stage build (uv + Python 3.12)
├── docker-compose.yml                      # Container orchestration
├── pyproject.toml                          # uv project config
├── .env.example                            # Environment template
└── LLM_AGGREGATOR_README.md                # LLM aggregation layer docs
```

---

## Configuration

Create a `.env` file:

```env
# Gemini API (for OCR extraction + LangChain validation)
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL_NAME="gemini-3-flash-preview"

# OpenAI (optional, for CrewAI if enabled)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL_NAME="gpt-5-mini"

# API server
API_HOST=0.0.0.0
API_PORT=8000

# Optional
CREWAI_TRACING_ENABLED=true
```

---

## Job Status Flow

```
UPLOADED ──► EXTRACTING ──► VALIDATING ──► COMPLETED
                 │                │
                 └────► FAILED ◄──┘
```

---

## Response Schema

```json
{
  "job_id": "PAT-edce340e42b8",
  "status": "COMPLETED",
  "created_at": "2026-01-25T10:15:26.166367",
  "started_at": "2026-01-25T10:15:50.474445",
  "completed_at": "2026-01-25T10:18:58.813960",
  "error": null,
  "extracted_data": {
    "patient": { "name": "Omar Mohamed Hatem", "age": "6.5 years", "gender": "Male" },
    "diagnosis": { "primary": "Allergic Rhinitis", "icd_code": "J30.9" },
    "medications": [
      { "name": "Azulast phys N. spray", "dosage": "One puff twice daily", "duration": "One month" }
    ]
  },
  "result": {
    "transaction_id": "REQ-2026-5DD7",
    "timestamp": "2026-01-25T10:18:58.813441",
    "patient_profile": {
      "id": "PAT-edce340e42b8",
      "name": "Omar Mohamed Hatem",
      "age": "6",
      "gender": "Male"
    },
    "ai_validation_engine": {
      "overall_status": "APPROVED",
      "confidence_score": "1.0",
      "medication_count": "3",
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
            "reason_ar": "مناسب سريرياً للتشخيص"
          }
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
| API | FastAPI (async) |
| OCR Extraction | Google Gemini Vision (GenAI SDK) |
| Validation | LangChain + Gemini Structured Output |
| Schema | Pydantic v2 |
| Logging | Loguru |
| Package Manager | uv |
| Container | Docker (multi-stage, non-root) |
| Python | 3.12+ |

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Async web framework |
| `google-genai` | Gemini API client (OCR extraction) |
| `langchain` + `langchain-google-genai` | LLM orchestration with structured output |
| `pydantic` | Data validation and schema enforcement |
| `loguru` | Structured logging |
| `aiofiles` | Async file I/O |
| `uvicorn` | ASGI server |