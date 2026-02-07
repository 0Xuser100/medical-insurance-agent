# API Contract: Upload Response

**Endpoint**: `POST /upload`
**Feature**: Fix Photo Upload Schema Mismatch
**Version**: 1.0
**Status**: Active

---

## Contract Overview

This contract defines the response schema for the file upload endpoint. It ensures alignment between the backend (Python/FastAPI/Pydantic) and frontend (TypeScript/Next.js/Zod) implementations.

---

## Endpoint Details

### Request

**Method**: `POST`
**Path**: `/upload`
**Content-Type**: `multipart/form-data`

**Request Body**:
```
file: binary (image file)
```

**Constraints**:
- File size: Max 10MB
- Allowed types: `image/jpeg`, `image/jpg`, `image/png`
- Field name must be `file`

### Response

**Status Code**: `200 OK`
**Content-Type**: `application/json`

**Response Body**:
```json
{
  "job_id": "string (UUID)",
  "status": "string (enum)",
  "filename": "string",
  "file_size": "number (integer, bytes)",
  "created_at": "string (ISO 8601 datetime)",
  "message": "string"
}
```

---

## Field Specifications

### job_id
- **Type**: `string`
- **Format**: UUID v4
- **Required**: Yes
- **Description**: Unique identifier for the processing job
- **Example**: `"550e8400-e29b-41d4-a716-446655440000"`
- **Constraints**:
  - Must be valid UUID format
  - Must be unique across all jobs
  - Used for subsequent job status queries

### status
- **Type**: `string` (enum)
- **Required**: Yes
- **Allowed Values**:
  - `"UPLOADED"` - Initial state after successful upload
  - `"PROCESSING"` - Job is being processed (not set on upload)
  - `"COMPLETED"` - Processing finished successfully (not set on upload)
  - `"FAILED"` - Processing failed (not set on upload)
- **Default**: `"UPLOADED"`
- **Description**: Current status of the processing job
- **Example**: `"UPLOADED"`
- **Constraints**:
  - For successful upload responses, value MUST be `"UPLOADED"`
  - Case-sensitive

### filename
- **Type**: `string`
- **Required**: Yes
- **Description**: Original filename from the uploaded file
- **Example**: `"prescription_scan_2026.jpg"`
- **Constraints**:
  - Must match the original uploaded filename
  - Must not be empty
  - Should preserve file extension
  - Maximum length: 255 characters

### file_size
- **Type**: `number` (integer)
- **Required**: Yes
- **Unit**: Bytes
- **Description**: Size of the uploaded file in bytes
- **Example**: `245768` (equivalent to 245.8 KB)
- **Constraints**:
  - Must be positive integer
  - Must match actual file size
  - Minimum: 1 byte
  - Maximum: 10,485,760 bytes (10 MB)

### created_at
- **Type**: `string`
- **Format**: ISO 8601 datetime with timezone
- **Required**: Yes
- **Description**: Timestamp when the upload was created
- **Example**: `"2026-02-07T14:23:45.123456Z"`
- **Constraints**:
  - Must be valid ISO 8601 format
  - Should include timezone (UTC recommended)
  - Should include milliseconds/microseconds for precision

### message
- **Type**: `string`
- **Required**: Yes
- **Description**: User-facing status message
- **Example**: `"File uploaded successfully"`
- **Default**: `"File uploaded successfully"`
- **Constraints**:
  - Must not be empty
  - Should be in English (bilingual support future enhancement)
  - Maximum length: 500 characters

---

## Validation Rules

### Backend Validation (Pydantic)

```python
class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.UPLOADED)
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes", gt=0)
    created_at: datetime = Field(default_factory=datetime.now)
    message: str = Field(default="File uploaded successfully")

    @validator('job_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('job_id must be valid UUID')
        return v

    @validator('file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('file_size must be positive')
        if v > 10_485_760:
            raise ValueError('file_size exceeds 10MB limit')
        return v
```

### Frontend Validation (Zod)

```typescript
export const UploadResponseSchema = z.object({
  job_id: z.string().uuid('Invalid UUID format'),
  status: z.enum(['UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED']),
  filename: z.string().min(1, 'Filename is required').max(255),
  file_size: z.number()
    .int('File size must be integer')
    .positive('File size must be positive')
    .max(10_485_760, 'File size exceeds 10MB'),
  created_at: z.string().datetime('Invalid ISO 8601 datetime'),
  message: z.string().min(1, 'Message is required').max(500),
});
```

---

## Example Responses

### Success Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "UPLOADED",
  "filename": "prescription_scan.jpg",
  "file_size": 245768,
  "created_at": "2026-02-07T14:23:45.123456Z",
  "message": "File uploaded successfully"
}
```

### Error Responses

#### 400 Bad Request - Invalid File Type
```json
{
  "detail": "Invalid file type. Allowed: image/jpeg, image/jpg, image/png"
}
```

#### 413 Payload Too Large - File Size Exceeded
```json
{
  "detail": "File size exceeds 10MB limit"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

---

## Contract Tests

### Backend Contract Test

**File**: `tests/contract/test_upload_schema.py`

```python
def test_upload_response_schema_contract():
    """Verify UploadResponse adheres to API contract."""
    response = UploadResponse(
        job_id="550e8400-e29b-41d4-a716-446655440000",
        status=JobStatus.UPLOADED,
        filename="test.jpg",
        file_size=12345,
        created_at=datetime.now(),
        message="File uploaded successfully"
    )

    # Serialize to JSON (what frontend receives)
    json_str = response.model_dump_json()
    data = json.loads(json_str)

    # Verify contract fields
    assert "job_id" in data
    assert "status" in data
    assert "filename" in data
    assert "file_size" in data
    assert "created_at" in data
    assert "message" in data

    # Verify types
    assert isinstance(data["job_id"], str)
    assert isinstance(data["status"], str)
    assert isinstance(data["filename"], str)
    assert isinstance(data["file_size"], int)
    assert isinstance(data["created_at"], str)
    assert isinstance(data["message"], str)

    # Verify UUID format
    uuid.UUID(data["job_id"])

    # Verify enum value
    assert data["status"] in ["UPLOADED", "PROCESSING", "COMPLETED", "FAILED"]
```

### Frontend Contract Test

**File**: `medical-insurance-frontend/__tests__/lib/schemas/upload-response.contract.test.ts`

```typescript
describe('Upload Response Contract', () => {
  it('validates response matching backend contract', () => {
    const backendResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'UPLOADED',
      filename: 'test.jpg',
      file_size: 12345,
      created_at: '2026-02-07T14:23:45.123456Z',
      message: 'File uploaded successfully',
    };

    const result = UploadResponseSchema.safeParse(backendResponse);

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.job_id).toMatch(/^[0-9a-f-]{36}$/i);
      expect(result.data.status).toBe('UPLOADED');
      expect(result.data.file_size).toBeGreaterThan(0);
    }
  });

  it('rejects response missing required fields', () => {
    const invalidResponse = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'UPLOADED',
      // Missing: filename, file_size, created_at, message
    };

    const result = UploadResponseSchema.safeParse(invalidResponse);

    expect(result.success).toBe(false);
    if (!result.success) {
      const missingFields = result.error.issues.map(i => i.path[0]);
      expect(missingFields).toContain('filename');
      expect(missingFields).toContain('file_size');
      expect(missingFields).toContain('message');
    }
  });
});
```

---

## Schema Evolution

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-07 | Initial contract definition, aligned with backend implementation |

### Future Changes (Proposed)

#### Optional Fields for Future Enhancement
If the backend adds these fields in the future, they should be made optional:

```typescript
// Future enhancement (example)
export const UploadResponseSchemaV2 = UploadResponseSchema.extend({
  thumbnail_url: z.string().url().optional(), // Optional: preview URL
  detected_language: z.enum(['en', 'ar']).optional(), // Optional: OCR language detection
});
```

### Breaking Change Policy

**Breaking changes** (changes that would cause existing frontends to fail validation):
- Removing required fields
- Changing field types
- Renaming fields
- Making optional fields required

**Non-breaking changes** (safe to add without versioning):
- Adding optional fields
- Relaxing validation constraints
- Adding new enum values (if handled gracefully)

---

## Compliance Checklist

- ✅ All required fields documented
- ✅ Field types specified
- ✅ Validation rules defined
- ✅ Example responses provided
- ✅ Error responses documented
- ✅ Contract tests defined
- ✅ Backend implementation matches contract
- ⏳ Frontend implementation pending (Phase 2)
- ⏳ Contract tests pending (Phase 2)

---

## Related Contracts

- **Job Status Query**: `GET /jobs/{job_id}` - Returns detailed job status with `started_at`, `completed_at`, `error` fields
- **Process Request**: `POST /process` - Triggers processing for an uploaded job

---

## Maintainers

- Backend: Medical Insurance Agent Team
- Frontend: Medical Insurance Agent Team
- Contract Owner: Feature 002-fix-photo-upload

---

**Contract Status**: ✅ Defined and Ready
**Implementation Status**: ⏳ Pending Phase 2
**Last Updated**: 2026-02-07
