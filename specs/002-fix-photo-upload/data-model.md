# Data Model: Upload Response Schema Alignment

**Feature**: Fix Photo Upload Schema Mismatch
**Date**: 2026-02-07
**Status**: Design Complete

---

## Overview

This document defines the `UploadResponse` entity and its schema alignment between backend (Python Pydantic) and frontend (TypeScript Zod). The fix resolves a schema mismatch that causes successful uploads to appear as failures.

---

## Entity: UploadResponse

### Purpose
Represents the immediate response returned when a user uploads a prescription photo. Contains metadata about the uploaded file and the processing job created for it.

### Lifecycle
1. User uploads file via frontend
2. Backend saves file and creates processing job
3. Backend returns `UploadResponse` immediately
4. Frontend validates response with Zod schema
5. UI displays success message with upload details

### Relationships
- **Job Status**: The `job_id` can be used to query job status endpoint for processing updates
- **File Storage**: The `filename` corresponds to the file saved in `uploads/` directory
- **User Session**: Upload is associated with current user session (authentication context)

---

## Schema Definition

### Backend Schema (Source of Truth)

**Location**: `src/models/schemas.py` (lines 223-236)

```python
class UploadResponse(BaseModel):
    """Response from file upload endpoint."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.UPLOADED, description="Job status")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Upload timestamp"
    )
    message: str = Field(
        default="File uploaded successfully", description="Status message"
    )
```

**Serialization Example**:
```json
{
  "job_id": "a3f2c8b1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "status": "UPLOADED",
  "filename": "prescription_scan.jpg",
  "file_size": 245768,
  "created_at": "2026-02-07T14:23:45.123456",
  "message": "File uploaded successfully"
}
```

### Frontend Schema (Current - INCORRECT)

**Location**: `medical-insurance-frontend/lib/schemas/validation.ts` (lines 111-119)

```typescript
// ❌ CURRENT (INCORRECT) - Causes validation to fail
export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),   // ❌ NOT in backend response
  completed_at: z.string().nullable(), // ❌ NOT in backend response
  error: z.string().nullable(),        // ❌ NOT in backend response
});
```

**Problem**: Zod validation fails because backend returns `filename`, `file_size`, and `message`, but schema doesn't expect them.

### Frontend Schema (Target - CORRECT)

**Location**: `medical-insurance-frontend/lib/schemas/validation.ts`

```typescript
// ✅ CORRECTED - Aligns with backend
export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  filename: z.string(),
  file_size: z.number(),
  created_at: z.string(),
  message: z.string(),
});

export type UploadResponse = z.infer<typeof UploadResponseSchema>;
```

**Note**: The fields `started_at`, `completed_at`, and `error` belong to the **Job Status** response (different endpoint), not the Upload response.

---

## Field Specifications

### job_id
- **Type**: `string` (UUID format)
- **Required**: Yes
- **Description**: Unique identifier for the processing job created for this upload
- **Example**: `"a3f2c8b1-4d5e-6f7a-8b9c-0d1e2f3a4b5c"`
- **Usage**: Used to query job status endpoint (`GET /jobs/{job_id}`) for processing updates
- **Validation**: Should be valid UUID format

### status
- **Type**: `JobStatus` enum
- **Required**: Yes
- **Possible Values**: `"UPLOADED"`, `"PROCESSING"`, `"COMPLETED"`, `"FAILED"`
- **Description**: Current status of the job
- **Default**: `"UPLOADED"` for new uploads
- **Usage**: Indicates whether upload is complete and ready for processing

### filename
- **Type**: `string`
- **Required**: Yes
- **Description**: Original filename provided by the user
- **Example**: `"prescription_scan.jpg"`
- **Usage**: Displayed in UI to confirm which file was uploaded
- **Validation**: Should match uploaded file's original name

### file_size
- **Type**: `number` (integer, bytes)
- **Required**: Yes
- **Description**: Size of the uploaded file in bytes
- **Example**: `245768` (245.8 KB)
- **Usage**: Displayed in UI for user confirmation, logged for auditing
- **Validation**: Must be positive integer

### created_at
- **Type**: `string` (ISO 8601 datetime)
- **Required**: Yes
- **Description**: Timestamp when the upload was created
- **Example**: `"2026-02-07T14:23:45.123456"`
- **Backend Format**: Python `datetime` serialized to ISO 8601
- **Frontend Parsing**: Can be parsed with `new Date(created_at)`
- **Usage**: Displayed in UI, used for sorting/filtering uploads

### message
- **Type**: `string`
- **Required**: Yes
- **Description**: User-facing status message
- **Example**: `"File uploaded successfully"`
- **Default**: `"File uploaded successfully"` (backend default)
- **Usage**: Displayed directly in UI as success feedback
- **Localization**: Currently English only, could be extended for bilingual support

---

## Related Entities

### JobStatus (Separate Schema)

**Location**: `medical-insurance-frontend/lib/schemas/validation.ts`

```typescript
// This is for GET /jobs/{job_id} endpoint, NOT upload endpoint
export const JobStatusResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),    // ✅ Correct for job status
  completed_at: z.string().nullable(),  // ✅ Correct for job status
  error: z.string().nullable(),         // ✅ Correct for job status
  result: z.unknown().nullable(),       // Processing result
});
```

**Note**: The fields `started_at`, `completed_at`, and `error` are appropriate for **job status queries**, not upload responses. These were incorrectly used in the upload schema.

---

## Schema Alignment Matrix

| Field | Backend (Pydantic) | Frontend (Current) | Frontend (Fixed) | Status |
|-------|-------------------|-------------------|------------------|--------|
| `job_id` | ✅ string | ✅ string | ✅ string | Aligned |
| `status` | ✅ JobStatus | ✅ JobStatus | ✅ JobStatus | Aligned |
| `filename` | ✅ string | ❌ Missing | ✅ string | **FIX REQUIRED** |
| `file_size` | ✅ number | ❌ Missing | ✅ number | **FIX REQUIRED** |
| `created_at` | ✅ datetime | ✅ string | ✅ string | Aligned |
| `message` | ✅ string | ❌ Missing | ✅ string | **FIX REQUIRED** |
| `started_at` | ❌ Not present | ❌ Wrong schema | ❌ Remove | **FIX REQUIRED** |
| `completed_at` | ❌ Not present | ❌ Wrong schema | ❌ Remove | **FIX REQUIRED** |
| `error` | ❌ Not present | ❌ Wrong schema | ❌ Remove | **FIX REQUIRED** |

---

## Validation Rules

### Backend Validation (Pydantic)
```python
# Handled by Pydantic Field constraints
- job_id: Required, non-empty string
- status: Must be valid JobStatus enum value
- filename: Required, non-empty string
- file_size: Required, positive integer
- created_at: Valid datetime, defaults to current time
- message: Required, defaults to success message
```

### Frontend Validation (Zod)
```typescript
// After fix
export const UploadResponseSchema = z.object({
  job_id: z.string().uuid(), // Optional: enforce UUID format
  status: JobStatusSchema,
  filename: z.string().min(1), // Non-empty filename
  file_size: z.number().positive(), // Must be positive
  created_at: z.string().datetime(), // ISO 8601 format
  message: z.string().min(1), // Non-empty message
});
```

---

## Example Scenarios

### Successful Upload
```typescript
// Backend response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "UPLOADED",
  "filename": "my_prescription.png",
  "file_size": 1048576,
  "created_at": "2026-02-07T10:30:00Z",
  "message": "File uploaded successfully"
}

// Frontend validation (after fix)
const result = UploadResponseSchema.safeParse(response);
// ✅ result.success === true
// ✅ UI displays: "Successfully uploaded my_prescription.png (1.0 MB)"
```

### Failed Validation (Before Fix)
```typescript
// Backend response (same as above)
const result = UploadResponseSchema.safeParse(response);
// ❌ result.success === false
// ❌ result.error.issues: "filename" is unexpected, "started_at" is required
// ❌ UI displays: "Upload failed" (even though upload succeeded!)
```

---

## Migration Impact

### Files to Modify
1. ✅ **Frontend schema**: `medical-insurance-frontend/lib/schemas/validation.ts`
   - Update `UploadResponseSchema` with correct fields
   - Remove incorrect fields
   - Add validation rules

2. ⚠️ **Upload component**: `medical-insurance-frontend/components/features/upload/UploadZone.tsx`
   - Update to display `filename` and `file_size` in success message
   - Use `message` field for status text
   - Handle new response shape

3. ❌ **Backend**: No changes required (already correct)

### Breaking Changes
**None**. This is a frontend-only fix that aligns validation with existing backend behavior.

### Backward Compatibility
- New schema matches backend response exactly
- No API version changes required
- Existing uploads continue to work
- No data migration needed

---

## Testing Requirements

### Unit Tests
```typescript
// tests/schemas/upload-response.test.ts
describe('UploadResponseSchema', () => {
  it('validates correct upload response', () => {
    const validResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'UPLOADED',
      filename: 'test.jpg',
      file_size: 12345,
      created_at: '2026-02-07T10:30:00Z',
      message: 'File uploaded successfully',
    };

    const result = UploadResponseSchema.safeParse(validResponse);
    expect(result.success).toBe(true);
  });

  it('rejects response with missing filename', () => {
    const invalidResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'UPLOADED',
      // Missing filename, file_size, message
      created_at: '2026-02-07T10:30:00Z',
    };

    const result = UploadResponseSchema.safeParse(invalidResponse);
    expect(result.success).toBe(false);
  });
});
```

### Integration Tests
```typescript
// tests/integration/upload.test.ts
it('successfully uploads file and parses response', async () => {
  const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
  const response = await uploadPrescription(file);

  // Should not throw validation error
  const validated = UploadResponseSchema.parse(response);

  expect(validated.filename).toBe('test.jpg');
  expect(validated.file_size).toBeGreaterThan(0);
  expect(validated.message).toBeTruthy();
});
```

---

## Status

- ✅ Schema design complete
- ✅ Validation rules defined
- ✅ Testing strategy documented
- ⏳ Implementation pending (Phase 2)
- ⏳ Tests pending (Phase 2)

**Ready for**: Task generation (`/speckit.tasks`)
