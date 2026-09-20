# Medical Insurance Validation System

![SmartClaim — AI Medical Insurance Claim Validation](assets/banner.webp)

AI-powered prescription validation system with a **Next.js frontend** and **FastAPI backend** that processes prescription images/PDFs and generates structured approval/rejection reports with bilingual support (EN/AR) and real-time status tracking.

---

## Quick Start

### Full Stack (Backend + Frontend)

**Backend (FastAPI)**
```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env  # Edit with your Gemini API key

# 3. Run backend
uv run uvicorn src.api.main:app --reload
# API available at: http://localhost:8000
```

**Frontend (Next.js)**
```bash
# 1. Navigate to frontend
cd medical-insurance-frontend

# 2. Install dependencies
npm install

# 3. Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 4. Run dev server
npm run dev
# Frontend available at: http://localhost:3000
```

### Docker (Backend Only)

```bash
# 1. Configure environment
cp .env.example .env  # Edit with your API keys

# 2. Build and run
docker compose up --build

# 3. Stop
docker compose down
```

**Access Points:**
- **Frontend**: http://localhost:3000 (English) | http://localhost:3000/ar (Arabic)
- **Backend API**: http://localhost:8000/docs (Swagger UI)



## Architecture

### Full Stack Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                          │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ Upload Zone   │─▶│ Status Track │─▶│  Results Display          │ │
│  │ Drag & Drop   │  │ Auto-Polling │  │  • Patient Info           │ │
│  │ File Validate │  │ Progress UI  │  │  • Medications (badges)   │ │
│  └───────────────┘  └──────────────┘  │  • Labs, Diagnosis        │ │
│                                        │  • Bilingual (EN/AR + RTL)│ │
│  React Query • next-intl • Zustand    └───────────────────────────┘ │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ REST API
┌─────────────────────────────▼────────────────────────────────────────┐
│                       BACKEND (FastAPI)                               │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────────┐           │
│  │   UPLOAD    │──▶│   EXTRACT   │──▶│    VALIDATE      │           │
│  │  Image/PDF  │   │ Gemini OCR  │   │ LangChain+Gemini │           │
│  │  Job Store  │   │ (GenAI SDK) │   │ Structured Output│           │
│  └─────────────┘   └─────────────┘   └──────────────────┘           │
│                                                                       │
│  FastAPI • Pydantic • async/await • LangChain                        │
└───────────────────────────────────────────────────────────────────────┘
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

## Frontend Features

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 16 (App Router, Turbopack) |
| UI | React 19, Tailwind CSS v4 |
| State | TanStack Query (server), Zustand (client) |
| i18n | next-intl (EN/AR with RTL) |
| Forms | react-dropzone |
| Validation | Zod v4 (runtime schema validation) |
| Type Safety | TypeScript (strict mode) |

### Core Features

**✅ Upload Prescription** (`/`)
- Drag & drop or browse file selection
- File validation (JPEG, PNG, GIF, WebP, TIFF, PDF, max 10MB)
- Auto-upload → process → redirect flow
- Error handling with user feedback

**✅ Status Tracking** (`/prescriptions/status`)
- Real-time progress indicators (UPLOADED → EXTRACTING → VALIDATING → COMPLETED)
- Auto-polling every 3 seconds (stops on completion/failure)
- Retry on failure
- Auto-navigation to results on completion

**✅ Results Display** (`/prescriptions/[jobId]`)
- Overall validation status with confidence score
- Patient information card with avatar
- Medication cards with:
  - Approval/rejection badges
  - Risk level indicators (LOW/MEDIUM/HIGH)
  - Bilingual AI reasoning (EN/AR)
  - Clinical match indicators
- Extracted diagnosis and labs
- Provider information
- Transaction ID and timestamp

**✅ Bilingual Support**
- Full English and Arabic translations
- RTL layout for Arabic (`/ar` routes)
- Language switcher in header (EN/AR)
- Locale-aware formatting

**✅ Accessibility**
- WCAG 2.1 AA compliant focus indicators
- Semantic HTML with ARIA labels
- Keyboard navigation support
- Loading states and error boundaries

### Frontend Structure

```
medical-insurance-frontend/
├── app/[locale]/                       # Next.js App Router
│   ├── layout.tsx                      # Root layout (i18n + RTL)
│   ├── page.tsx                        # Home (upload)
│   ├── error.tsx                       # Error boundary
│   ├── not-found.tsx                   # 404 page
│   └── prescriptions/
│       ├── [jobId]/
│       │   ├── page.tsx                # Results page
│       │   └── loading.tsx             # Loading skeleton
│       └── status/
│           └── page.tsx                # Status tracker
├── components/
│   ├── features/
│   │   ├── upload/UploadZone.tsx       # Drag & drop upload
│   │   ├── prescription/               # Result display components
│   │   │   ├── ResultCard.tsx          # Overall summary
│   │   │   ├── PatientHeader.tsx       # Patient info
│   │   │   ├── MedicationCard.tsx      # Line item card
│   │   │   ├── DiagnosisCard.tsx       # Diagnosis display
│   │   │   ├── LabsCard.tsx            # Labs table
│   │   │   ├── ProviderCard.tsx        # Provider info
│   │   │   ├── StatusBadge.tsx         # Status/risk badges
│   │   │   └── ResultSkeleton.tsx      # Loading state
│   │   └── layout/                     # Layout components
│   │       ├── Header.tsx              # App header
│   │       ├── Footer.tsx              # App footer
│   │       └── LanguageSwitcher.tsx    # EN/AR toggle
│   └── providers/
│       └── QueryProvider.tsx           # TanStack Query wrapper
├── lib/
│   ├── api/
│   │   ├── client.ts                   # Fetch wrapper
│   │   ├── queries.ts                  # useJobResult, useJobStatus
│   │   └── mutations.ts                # useUploadPrescription, useProcessJob
│   ├── schemas/validation.ts           # Zod schemas (mirror backend)
│   ├── stores/useLanguageStore.ts      # Zustand locale store
│   └── utils/
│       ├── cn.ts                       # Tailwind class merger
│       └── formatters.ts               # Date, confidence formatters
├── i18n/
│   ├── routing.ts                      # Locale config
│   ├── request.ts                      # Server-side i18n
│   └── navigation.ts                   # Client-side navigation
├── messages/
│   ├── en.json                         # English translations
│   └── ar.json                         # Arabic translations
├── styles/globals.css                  # Tailwind v4 + theme tokens
├── middleware.ts                       # next-intl middleware
├── next.config.ts                      # Next.js config
├── tsconfig.json                       # TypeScript config
├── package.json                        # Dependencies
└── .env.local                          # Environment (NEXT_PUBLIC_API_URL)
```

### Development Commands

```bash
cd medical-insurance-frontend

npm run dev         # Start dev server (http://localhost:3000)
npm run build       # Production build
npm run start       # Production server
npm run lint        # ESLint
npm run type-check  # TypeScript validation
```

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
├── medical-insurance-frontend/             # Next.js 16 Frontend
│   ├── app/[locale]/                       # Next.js App Router (locale-aware)
│   ├── components/                         # React components
│   │   ├── features/                       # Feature components (upload, prescription, layout)
│   │   └── providers/                      # Context providers (QueryProvider)
│   ├── lib/                                # Business logic
│   │   ├── api/                            # API client (queries, mutations)
│   │   ├── schemas/                        # Zod validation schemas
│   │   ├── stores/                         # Zustand stores
│   │   └── utils/                          # Utilities (formatters, cn)
│   ├── i18n/                               # Internationalization (routing, request, navigation)
│   ├── messages/                           # Translations (en.json, ar.json)
│   ├── styles/                             # Tailwind CSS v4
│   ├── public/                             # Static assets
│   ├── next.config.ts                      # Next.js configuration
│   ├── middleware.ts                       # next-intl middleware
│   ├── tsconfig.json                       # TypeScript config
│   ├── package.json                        # npm dependencies
│   └── .env.local                          # Environment (NEXT_PUBLIC_API_URL)
│
├── src/                                    # FastAPI Backend
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
│
├── tests/                                  # Backend tests
│   ├── __init__.py
│   ├── test_api_schema.py                  # API endpoint schema tests
│   └── test_validators.py                  # Validator tests
│
├── specs/                                  # Speckit feature specifications
│   └── 001-prescription-ui/                # Frontend spec (v1.0.0)
│       ├── spec.md                         # User stories and requirements
│       ├── plan.md                         # Implementation plan
│       ├── tasks.md                        # 90 tasks across 8 phases
│       ├── research.md                     # Technology research
│       ├── data-model.md                   # TypeScript/Zod schemas
│       ├── quickstart.md                   # Developer setup guide
│       └── contracts/                      # API contracts
│
├── .specify/                               # Speckit framework
│   └── memory/
│       └── constitution.md                 # Project constitution (5 principles)
│
├── uploads/                                # Uploaded files (runtime)
├── Dockerfile                              # Multi-stage build (uv + Python 3.12)
├── docker-compose.yml                      # Container orchestration
├── pyproject.toml                          # uv project config
├── .env.example                            # Backend environment template
└── README.md                               # This file
```

---

## Development Workflow

### Running Both Backend + Frontend

**Terminal 1 - Backend:**
```bash
# From project root
uv run uvicorn src.api.main:app --reload
# Backend running at http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
# From project root
cd medical-insurance-frontend
npm run dev
# Frontend running at http://localhost:3000
```

### Testing the Complete Flow

1. **Open Frontend**: http://localhost:3000
2. **Upload**: Drag & drop a prescription image (JPEG/PNG/PDF)
3. **Track**: Auto-redirected to status page with progress indicators
4. **View Results**: Auto-navigate to results when processing completes
5. **Switch Language**: Use EN/AR toggle in header (RTL layout for Arabic)

### API Integration

The frontend uses these environment variables:

```env
# medical-insurance-frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The frontend automatically:
- Uploads files to `/upload`
- Triggers processing via `/process`
- Polls status via `/job/{job_id}` every 3 seconds
- Fetches final results from `/result/{job_id}`

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

## Client Integration

### Official Frontend

This project includes a production-ready **Next.js frontend** in `medical-insurance-frontend/`.

See the [Frontend Features](#frontend-features) section above for details.

### Custom Integration (JavaScript/TypeScript)

If building a custom client, use this integration pattern:

```typescript
// Using TanStack Query (recommended - from our Next.js frontend)
import { useMutation, useQuery } from "@tanstack/react-query";

// 1. Upload mutation
const uploadMutation = useMutation({
  mutationFn: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });
    return res.json();
  },
});

// 2. Status polling query
const { data } = useQuery({
  queryKey: ["job-status", jobId],
  queryFn: async () => {
    const res = await fetch(`http://localhost:8000/job/${jobId}`);
    return res.json();
  },
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    if (status === "COMPLETED" || status === "FAILED") return false;
    return 3000; // Poll every 3 seconds
  },
});
```

**Vanilla JavaScript:**

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
  await new Promise(r => setTimeout(r, 3000)); // Poll every 3s
}
```

---

## Technology Stack

### Backend

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

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | Next.js 16 (App Router, Turbopack) |
| UI Library | React 19 |
| Styling | Tailwind CSS v4 |
| State Management | TanStack Query v5 (server), Zustand v5 (client) |
| i18n | next-intl v4 (EN/AR with RTL) |
| Forms | react-dropzone v14 |
| Validation | Zod v4 |
| Type Safety | TypeScript 5.9 (strict mode) |
| Package Manager | npm |
| Build Tool | Turbopack (Next.js 16) |

---

## Key Dependencies

### Backend

| Package | Purpose |
|---------|---------|
| `fastapi` | Async web framework |
| `google-genai` | Gemini API client (OCR extraction) |
| `langchain` + `langchain-google-genai` | LLM orchestration with structured output |
| `pydantic` | Data validation and schema enforcement |
| `loguru` | Structured logging |
| `aiofiles` | Async file I/O |
| `uvicorn` | ASGI server |

### Frontend

| Package | Purpose |
|---------|---------|
| `next` | React framework with App Router |
| `react` + `react-dom` | UI library |
| `@tanstack/react-query` | Server state management with auto-polling |
| `next-intl` | Internationalization (i18n) with locale routing |
| `zustand` | Client state management |
| `zod` | Runtime schema validation |
| `react-dropzone` | File upload with drag & drop |
| `tailwindcss` | Utility-first CSS framework |
| `clsx` + `tailwind-merge` | Conditional class name utilities |