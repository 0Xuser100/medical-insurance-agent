# Feature Specification: Fix Photo Upload Schema Mismatch

**Feature Branch**: `002-fix-photo-upload`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "when i try to upload photo it refuse upload photo"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Successful Photo Upload (Priority: P1)

A user needs to upload a prescription photo to initiate medical insurance verification. Currently, uploads appear to fail even when the backend successfully processes the file, due to a schema validation mismatch between frontend and backend response formats.

**Why this priority**: This is a critical blocker preventing users from completing the primary workflow. Without functional photo uploads, the entire application is unusable.

**Independent Test**: Can be fully tested by uploading a valid image file (PNG/JPG/JPEG) through the upload interface and verifying the success message displays correctly with upload details.

**Acceptance Scenarios**:

1. **Given** a user has a valid prescription image file, **When** they drag and drop or select the file in the upload zone, **Then** the file uploads successfully and displays a success message with the filename and file size
2. **Given** a user has uploaded a file successfully, **When** the upload completes, **Then** they can see the job ID and status information to track processing
3. **Given** a user uploads a file, **When** the backend processes it successfully, **Then** the frontend correctly parses the response and displays success feedback instead of an error

---

### User Story 2 - Clear Error Handling (Priority: P2)

When a photo upload genuinely fails (network error, server error, invalid file), users need to understand what went wrong so they can take corrective action.

**Why this priority**: While the primary issue is false failures, genuine error scenarios still need proper handling for a complete user experience.

**Independent Test**: Can be tested by simulating various error conditions (network disconnection, invalid file formats, oversized files) and verifying appropriate error messages display.

**Acceptance Scenarios**:

1. **Given** the server returns an error response, **When** the upload fails, **Then** the user sees a specific error message indicating the reason (not a generic "upload failed" message)
2. **Given** a file exceeds size limits or has an invalid format, **When** validation fails, **Then** the error message clearly explains the limitation and how to fix it
3. **Given** a network error occurs during upload, **When** the request times out, **Then** the user sees a retry option with a clear explanation

---

### Edge Cases

- What happens when the backend response schema evolves and adds new optional fields?
- How does the system handle partial responses or malformed JSON from the backend?
- What happens if the backend returns extra fields beyond the expected schema?
- How does the frontend handle null or missing optional fields in the response?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST correctly parse backend upload responses that include `filename`, `file_size`, and `message` fields
- **FR-002**: System MUST display upload success feedback showing the filename and file size to confirm the upload
- **FR-003**: System MUST align frontend response schema with backend `UploadResponse` schema structure
- **FR-004**: System MUST handle schema validation errors gracefully and provide specific error messages rather than generic failures
- **FR-005**: System MUST distinguish between validation errors (schema mismatch) and actual upload failures (network, server errors)
- **FR-006**: System MUST preserve backward compatibility if the backend schema adds new optional fields in the future

### Key Entities

- **UploadResponse**: The API response returned by the backend after a successful file upload, containing:
  - `job_id`: Unique identifier for the processing job
  - `status`: Current status of the upload/processing job
  - `filename`: Original name of the uploaded file
  - `file_size`: Size of the uploaded file in bytes
  - `created_at`: Timestamp when the upload was created
  - `message`: Success or status message from the backend

- **ValidationError**: Errors that occur when response data doesn't match the expected schema structure

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully upload prescription photos with a 100% success rate for valid files (no false failures due to schema mismatches)
- **SC-002**: Upload success messages display within 2 seconds of backend confirmation, showing filename and file size
- **SC-003**: Zero schema validation errors occur for valid backend responses that previously caused false upload failures
- **SC-004**: Error messages are specific and actionable, allowing users to understand and resolve actual upload failures within one attempt

## Assumptions & Dependencies *(mandatory)*

### Assumptions

- The backend `UploadResponse` schema in `src/models/schemas.py` is the source of truth and will not change during this fix
- The current backend response format (including `filename`, `file_size`, `message`) provides valuable information that should be preserved and displayed to users
- The upload functionality uses Zod for runtime type validation in the frontend
- File uploads are processed asynchronously with job tracking

### Dependencies

- Frontend validation schema file: `medical-insurance-frontend/lib/schemas/validation.ts`
- Backend schema definition: `src/models/schemas.py`
- Upload component: `medical-insurance-frontend/components/features/upload/UploadZone.tsx`
- API mutation handler: `medical-insurance-frontend/lib/api/mutations.ts`
- Backend upload endpoint: `src/api/main.py` (lines 53-78)

### Technical Context

The root cause has been identified as a schema mismatch:

**Backend Response** (`src/models/schemas.py` lines 223-236):
- Includes: `job_id`, `status`, `filename`, `file_size`, `created_at`, `message`

**Frontend Schema** (`lib/schemas/validation.ts` lines 111-119):
- Expects: `job_id`, `status`, `created_at`, `started_at`, `completed_at`, `error`
- Missing: `filename`, `file_size`, `message`
- Has extra: `started_at`, `completed_at`, `error` (not in backend initial response)

When the backend returns a successful upload with `filename` and `file_size`, the frontend Zod validation throws an error, causing uploads to appear as failures.

## Out of Scope

- Changes to file upload size limits or format restrictions
- Modifications to the backend upload processing logic or file storage
- UI/UX redesign of the upload component beyond displaying success information
- Performance optimization of upload speeds or chunked uploads
- Multiple file uploads or batch processing
- Image preview or thumbnail generation
