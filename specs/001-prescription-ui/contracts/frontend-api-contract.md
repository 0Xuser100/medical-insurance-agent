# Frontend API Contract

**Feature**: 001-prescription-ui
**Backend API**: Medical Insurance Validation API v1.0
**Base URL**: `http://localhost:8000` (dev), `https://api.mediscan.example.com` (prod)

---

## Overview

This document defines the API contract between the Next.js frontend and FastAPI backend. All requests use JSON (except file uploads which use multipart/form-data).

---

## Authentication

**Current**: No authentication required (per spec assumptions)
**Future**: Add Bearer token authentication when auth is implemented

```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Health Check

**Purpose**: Verify API availability

```
GET /health
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "api_version": "1.0.0"
}
```

**Frontend Usage**:
- App initialization health check
- Connection monitoring
- Error boundary fallback

---

### 2. Upload Prescription

**Purpose**: Upload prescription image/PDF and create job

```
POST /upload
Content-Type: multipart/form-data
```

**Request Body**:
```
file: <File> (JPEG, PNG, GIF, WebP, TIFF, PDF)
```

**Validation**:
- Max file size: 10MB
- Allowed MIME types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/tiff`, `application/pdf`

**Response** (200 OK):
```json
{
  "job_id": "PAT-b83c80a3c06a",
  "status": "UPLOADED",
  "created_at": "2026-02-07T13:45:24.243189",
  "started_at": null,
  "completed_at": null,
  "error": null
}
```

**Error Responses**:
- **400 Bad Request**: Invalid file type or size
  ```json
  {
    "detail": "File size exceeds 10MB limit"
  }
  ```
- **413 Payload Too Large**: File too large
- **500 Internal Server Error**: Server-side upload failure

**Frontend Implementation**:
```typescript
// lib/api/mutations.ts
export function useUploadPrescription() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      return UploadResponseSchema.parse(await response.json());
    }
  });
}
```

---

### 3. Process Prescription

**Purpose**: Initiate OCR extraction and validation

```
POST /process
Content-Type: application/json
```

**Request Body**:
```json
{
  "job_id": "PAT-b83c80a3c06a"
}
```

**Response** (200 OK):
```json
{
  "job_id": "PAT-b83c80a3c06a",
  "status": "PROCESSING",
  "message": "Processing started"
}
```

**Error Responses**:
- **404 Not Found**: job_id does not exist
- **409 Conflict**: Job already processing/completed

**Frontend Implementation**:
- Call immediately after successful upload
- No need for frontend-initiated call (backend handles automatically)
- Frontend only polls `/result/{job_id}`

---

### 4. Get Job Result

**Purpose**: Poll job status and retrieve results

```
GET /result/{job_id}
```

**Parameters**:
- `job_id`: string (path parameter, format: PAT-XXXXXXXXXXXX)

**Response** (200 OK - Processing):
```json
{
  "job_id": "PAT-b83c80a3c06a",
  "status": "EXTRACTING",
  "created_at": "2026-02-07T13:45:24.243189",
  "started_at": "2026-02-07T13:45:34.802106",
  "completed_at": null,
  "error": null,
  "extracted_data": null,
  "result": null
}
```

**Response** (200 OK - Completed):
```json
{
  "job_id": "PAT-b83c80a3c06a",
  "status": "COMPLETED",
  "created_at": "2026-02-07T13:45:24.243189",
  "started_at": "2026-02-07T13:45:34.802106",
  "completed_at": "2026-02-07T13:45:55.549870",
  "error": null,
  "extracted_data": {
    "patient": {
      "name": "Shaaban Khalil",
      "age": "41",
      "gender": "Male",
      "id": "not found"
    },
    "provider": {
      "name": "Mohamed Hassan Ali",
      "id": "not found",
      "facility": "DIMC"
    },
    "diagnosis": {
      "primary": "not found",
      "icd_code": "not found"
    },
    "medications": [
      {
        "name": "Solupred",
        "dosage": "20mg",
        "frequency": "1x2",
        "duration": "not found",
        "quantity": "not found"
      }
    ],
    "labs": [
      {
        "name": "ESR",
        "type": "not found"
      }
    ],
    "date": "16/1/2024"
  },
  "result": {
    "transaction_id": "REQ-2026-5E85",
    "timestamp": "2026-02-07T13:45:55.549647",
    "patient_profile": {
      "id": "PAT-b83c80a3c06a",
      "name": "Shaaban Khalil",
      "age": "41",
      "gender": "Male"
    },
    "ai_validation_engine": {
      "overall_status": "REJECTED",
      "confidence_score": "0.0",
      "medication_count": "2",
      "line_items": [
        {
          "type": "MEDICATION",
          "item_name": "Solupred",
          "status": "REJECTED",
          "ui_badge": "❌ Rejected",
          "risk_level": "HIGH",
          "validation_details": {
            "clinical_match": false,
            "duration_check": null,
            "reason_en": "No diagnosis provided in prescription - cannot validate medication appropriateness",
            "reason_ar": "لا يوجد تشخيص في الوصفة الطبية - لا يمكن التحقق من ملاءمة الدواء"
          }
        }
      ]
    }
  }
}
```

**Response** (200 OK - Failed):
```json
{
  "job_id": "PAT-b83c80a3c06a",
  "status": "FAILED",
  "created_at": "2026-02-07T13:45:24.243189",
  "started_at": "2026-02-07T13:45:34.802106",
  "completed_at": "2026-02-07T13:46:12.123456",
  "error": "OCR extraction failed: Image quality too low",
  "extracted_data": null,
  "result": null
}
```

**Error Responses**:
- **404 Not Found**: job_id does not exist
  ```json
  {
    "detail": "Job not found"
  }
  ```

**Frontend Implementation** (Auto-Polling):
```typescript
// hooks/usePrescriptionPolling.ts
export function usePrescriptionPolling(jobId: string | null) {
  return useQuery({
    queryKey: ['prescription', jobId],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/result/${jobId}`);
      if (!response.ok) throw new Error('Failed to fetch result');
      return JobResultResponseSchema.parse(await response.json());
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling when done
      if (status === 'COMPLETED' || status === 'FAILED') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
    retry: false
  });
}
```

---

### 5. Delete Job

**Purpose**: Cancel/delete a job and its files

```
DELETE /job/{job_id}
```

**Parameters**:
- `job_id`: string (path parameter)

**Response** (200 OK):
```json
{
  "message": "Job deleted successfully",
  "job_id": "PAT-b83c80a3c06a"
}
```

**Error Responses**:
- **404 Not Found**: job_id does not exist

**Frontend Usage**:
- User cancels upload during processing
- Clean up old jobs from list view

---

### 6. List Jobs

**Purpose**: Get all jobs with optional status filtering

```
GET /jobs?status={status}
```

**Query Parameters**:
- `status`: string (optional) - Filter by JobStatus enum

**Response** (200 OK):
```json
[
  {
    "job_id": "PAT-b83c80a3c06a",
    "status": "COMPLETED",
    "created_at": "2026-02-07T13:45:24.243189"
  },
  {
    "job_id": "PAT-xyz123abc456",
    "status": "PROCESSING",
    "created_at": "2026-02-07T14:00:12.456789"
  }
]
```

**Frontend Usage**:
- Job history page
- Admin dashboard
- User's past prescriptions list

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message in English",
  "detail_ar": "رسالة الخطأ بالعربية" // Optional
}
```

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Parse response with Zod schema |
| 400 | Bad Request (client error) | Show error message to user |
| 404 | Resource not found | Redirect to 404 page |
| 413 | Payload too large | Show file size error |
| 429 | Too many requests | Show rate limit warning |
| 500 | Server error | Show generic error + retry button |
| 503 | Service unavailable | Show "Service temporarily down" |

---

## Rate Limiting

**Current**: Not enforced
**Future**: 100 requests/minute per IP

**Frontend Response** (429 Too Many Requests):
```json
{
  "detail": "Rate limit exceeded. Please try again in 60 seconds."
}
```

**Frontend Handling**:
- Display countdown timer
- Disable upload button
- Show retry button after cooldown

---

## CORS Configuration

**Required Headers** (Backend):
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

---

## WebSocket (Future Enhancement)

**Purpose**: Real-time job status updates (eliminates polling)

```
WS /ws/job/{job_id}
```

**Server Messages**:
```json
{
  "type": "status_update",
  "job_id": "PAT-123",
  "status": "VALIDATING",
  "progress": 75
}
```

**Frontend Implementation** (Future):
```typescript
const socket = new WebSocket(`ws://localhost:8000/ws/job/${jobId}`);
socket.onmessage = (event) => {
  const update = JSON.parse(event.data);
  queryClient.setQueryData(['prescription', jobId], update);
};
```

---

## Performance Expectations

| Endpoint | Expected Response Time | Timeout |
|----------|------------------------|---------|
| GET /health | <50ms | 5s |
| POST /upload | <2s (10MB file) | 30s |
| POST /process | <100ms | 5s |
| GET /result/{job_id} | <200ms | 5s |
| DELETE /job/{job_id} | <100ms | 5s |
| GET /jobs | <500ms | 10s |

**Processing Times** (async):
- OCR Extraction: 5-15s
- AI Validation: 10-30s
- Total (upload → results): 20-50s

---

## Testing Contract

### Mock API Responses (MSW)

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('http://localhost:8000/upload', () => {
    return HttpResponse.json({
      job_id: 'PAT-test123',
      status: 'UPLOADED',
      created_at: new Date().toISOString(),
      started_at: null,
      completed_at: null,
      error: null
    });
  }),

  http.get('http://localhost:8000/result/:jobId', ({ params }) => {
    return HttpResponse.json({
      job_id: params.jobId,
      status: 'COMPLETED',
      extracted_data: { /* mock data */ },
      result: { /* mock validation */ }
    });
  })
];
```

---

## Security Considerations

1. **File Upload**:
   - Backend re-validates MIME type (don't trust client)
   - Scan uploaded files for malware
   - Store files outside web root

2. **Input Validation**:
   - Validate job_id format (regex: `^PAT-[a-f0-9]{12}$`)
   - Sanitize all user inputs

3. **Rate Limiting**:
   - Prevent DoS attacks on /upload
   - Throttle /result polling to 1 req/s per job_id

4. **CORS**:
   - Whitelist only production frontend domains
   - No `Access-Control-Allow-Origin: *` in production

---

## Versioning

**Current**: v1.0 (implicit, no version in URL)
**Future**: API versioning via URL path

```
/v1/upload
/v2/upload
```

**Frontend**: Use environment variable for API version
```env
NEXT_PUBLIC_API_VERSION=v1
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-07 | 1.0 | Initial contract for 001-prescription-ui feature |

---

## References

- Backend API README: `../../README.md`
- Backend Pydantic Schemas: `../../src/models/schemas.py`
- Frontend Data Model: `../data-model.md`
