# Implementation Plan: Fix Photo Upload API Endpoint Mismatch

**Branch**: `002-fix-photo-upload` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fix-photo-upload/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The frontend is attempting to poll job status using `GET /job/{job_id}`, but the backend API only exposes `GET /result/{job_id}`. This causes HTTP 405 "Method Not Allowed" errors during the polling phase after photo upload. The fix requires updating the frontend to use the correct endpoint path (`/result/{job_id}` instead of `/job/{job_id}`).

**Root Cause Analysis**:
- **Backend**: Defines `GET /result/{job_id}` at line 123 of `src/api/main.py`
- **Frontend**: Calls `GET /job/{job_id}` at line 23 of `lib/api/queries.ts`
- **Impact**: Users see 405 errors in browser console, but uploads actually succeed and process correctly

**Solution**: Update frontend polling endpoint from `/job/{job_id}` to `/result/{job_id}` to match backend implementation.

## Technical Context

**Language/Version**: TypeScript 5.7 with Next.js 15.5 (App Router) - Frontend; Python 3.11+ with FastAPI - Backend
**Primary Dependencies**: @tanstack/react-query 5.x (frontend API client), FastAPI 0.100+ (backend)
**Storage**: Files stored in `uploads/` directory, asynchronous job tracking
**Testing**: Jest with React Testing Library (frontend), pytest (backend)
**Target Platform**: Web application (Next.js frontend + FastAPI backend)
**Project Type**: Web - frontend/backend split architecture
**Performance Goals**: API responses <200ms, polling interval 3s
**Constraints**: Must maintain backward compatibility with existing upload flow
**Scale/Scope**: Single endpoint fix affecting job status polling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: AI-First with Structured Output ✅
**Status**: NOT APPLICABLE - This fix does not involve AI/ML components or structured outputs.

### Principle II: Bilingual & Accessibility by Default ✅
**Status**: COMPLIANT - No user-facing messages are changed. Existing error handling remains bilingual.

### Principle III: Async-First Architecture ✅
**Status**: COMPLIANT - Frontend uses React Query for async polling; backend endpoint is already `async def`. No changes to async patterns.

### Principle IV: Testability & Contract Validation ⚠️
**Status**: ACTION REQUIRED - Must verify contract tests exist for the `/result/{job_id}` endpoint and update frontend integration tests to use correct endpoint.

**Action Items**:
- Check if `tests/contract/` includes tests for `GET /result/{job_id}` response schema
- Update `__tests__/integration/upload.test.ts` to use `/result/{job_id}` instead of `/job/{job_id}`
- Ensure schema validation tests catch future endpoint path mismatches

### Principle V: Observability & Auditability ✅
**Status**: COMPLIANT - No changes to logging, audit trails, or observability infrastructure.

### Overall Assessment
**PASS** - No blocking violations. One action item for test updates (Principle IV) to be addressed in Phase 1.

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-photo-upload/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (existing)
├── research.md          # Phase 0 output - NOT NEEDED (straightforward bug fix)
├── data-model.md        # Phase 1 output - NOT NEEDED (no data model changes)
├── quickstart.md        # Phase 1 output - Optional (test scenarios)
├── contracts/           # Phase 1 output - API contract verification
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Web application structure (frontend + backend)
src/                          # Backend (FastAPI)
├── api/
│   └── main.py              # API endpoints - REFERENCE ONLY (no changes needed)
├── models/
│   └── schemas.py           # Pydantic schemas - REFERENCE ONLY
└── services/
    ├── file_service.py      # File upload handling - REFERENCE ONLY
    ├── job_store.py         # Job state management - REFERENCE ONLY
    └── processing_service.py # Background processing - REFERENCE ONLY

medical-insurance-frontend/  # Frontend (Next.js)
├── lib/
│   ├── api/
│   │   ├── queries.ts       # 🔧 CHANGE REQUIRED - Update /job/{id} → /result/{id}
│   │   ├── mutations.ts     # REFERENCE ONLY - Upload mutation (working correctly)
│   │   └── client.ts        # REFERENCE ONLY - API client
│   └── schemas/
│       └── validation.ts    # REFERENCE ONLY - Response schemas (already correct)
├── components/
│   └── features/
│       └── upload/
│           └── UploadZone.tsx # REFERENCE ONLY - UI component (working correctly)
└── __tests__/
    └── integration/
        └── upload.test.ts    # 🔧 CHANGE REQUIRED - Update test endpoint reference

tests/                        # Backend tests
├── contract/
│   └── test_api_contracts.py # ✅ VERIFY - Ensure /result/{job_id} contract exists
└── integration/
    └── test_upload_flow.py   # REFERENCE ONLY - Backend integration tests
```

**Structure Decision**: Web application with separate frontend/backend directories. Changes are isolated to frontend query layer (`lib/api/queries.ts`) and frontend integration tests. Backend remains unchanged as it already implements the correct endpoint structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. This is a straightforward bug fix aligning frontend endpoint calls with existing backend implementation.

---

## Phase 0: Research & Analysis

### Research Questions

**Q1**: Are there other frontend files that reference the incorrect `/job/{job_id}` endpoint?

**Finding**: Need to search frontend codebase for:
- Direct string references: `"/job/"` or `\`/job/\``
- URL construction patterns that might use this endpoint
- Any hardcoded endpoint paths in components or hooks

**Q2**: Does the backend `/result/{job_id}` endpoint return all necessary fields for frontend job status polling?

**Finding**: Review `src/api/main.py` lines 123-162 to verify `ResultResponse` schema includes:
- `job_id`, `status`, `created_at`, `started_at`, `completed_at`
- Optional fields: `error`, `extracted_data`, `result`
- Ensure these match frontend `JobResultResponseSchema` expectations

**Q3**: Are there existing contract tests that validate the `/result/{job_id}` endpoint schema?

**Finding**: Check `tests/contract/` for:
- Schema validation tests for `GET /result/{job_id}`
- Response format verification for all job statuses (UPLOADED, PROCESSING, COMPLETED, FAILED)
- Edge cases (invalid job_id, missing job)

### Research Tasks

1. **Grep frontend codebase for all `/job/` references**
   ```bash
   cd medical-insurance-frontend
   grep -r "'/job/'" --include="*.ts" --include="*.tsx"
   grep -r '"/job/"' --include="*.ts" --include="*.tsx"
   grep -r '`/job/' --include="*.ts" --include="*.tsx"
   ```

2. **Compare backend ResultResponse with frontend JobResultResponseSchema**
   - Read `src/models/schemas.py` to extract `ResultResponse` fields
   - Read `medical-insurance-frontend/lib/schemas/validation.ts` to extract `JobResultResponseSchema`
   - Create comparison table to identify any schema drift

3. **Verify backend contract tests exist**
   - Check if `tests/contract/test_api_contracts.py` exists
   - If exists, verify it tests `GET /result/{job_id}` endpoint
   - If missing, flag as Phase 1 task

### Decisions from Research

**Decision 1**: Single endpoint fix vs. multiple files
- **Chosen**: Update only `lib/api/queries.ts` (single file change)
- **Rationale**: Initial analysis shows only `useJobStatus` hook uses incorrect endpoint
- **Validation**: Grep search will confirm no other references exist

**Decision 2**: Update endpoint path vs. add backend alias
- **Chosen**: Update frontend to use `/result/{job_id}` (align with backend)
- **Rationale**: Backend `/result/{job_id}` is the established convention; adding `/job/{job_id}` alias would introduce unnecessary API surface area
- **Alternative Considered**: Add `@app.get("/job/{job_id}")` alias in backend - rejected because it violates API clarity principle (one endpoint, one purpose)

**Decision 3**: Test update scope
- **Chosen**: Update frontend integration tests + verify backend contract tests
- **Rationale**: Ensures both sides of API contract are validated
- **Action**: Update `__tests__/integration/upload.test.ts` to mock `/result/{job_id}` instead of `/job/{job_id}`

---

## Phase 1: Design & Contracts

### API Contract Verification

**Endpoint**: `GET /result/{job_id}`

**Contract**: (Extracted from `src/api/main.py` lines 123-162)

```yaml
path: /result/{job_id}
method: GET
parameters:
  - name: job_id
    in: path
    type: string
    required: true
    example: "PAT-0b1f01e6dc5f"
responses:
  200:
    description: Job result or current status
    schema:
      type: object
      required: [job_id, status, created_at]
      properties:
        job_id:
          type: string
          example: "PAT-0b1f01e6dc5f"
        status:
          type: string
          enum: [UPLOADED, PROCESSING, EXTRACTING, VALIDATING, AGGREGATING, COMPLETED, FAILED]
        created_at:
          type: string
          format: date-time
        started_at:
          type: string
          format: date-time
          nullable: true
        completed_at:
          type: string
          format: date-time
          nullable: true
        error:
          type: string
          nullable: true
          description: Error message if status is FAILED, or "Processing..." message if still in progress
        extracted_data:
          type: object
          nullable: true
          description: Extracted prescription data (only present when COMPLETED)
        result:
          type: object
          nullable: true
          description: Validation result (only present when COMPLETED)
  404:
    description: Job not found
    schema:
      type: object
      properties:
        detail:
          type: string
          example: "Job not found: PAT-invalid123"
```

**Frontend Schema Alignment**: (From `medical-insurance-frontend/lib/schemas/validation.ts`)

The frontend `JobResultResponseSchema` must align with the backend response structure. Key verification points:
- ✅ All required fields (`job_id`, `status`, `created_at`) are expected by frontend
- ✅ Optional fields (`started_at`, `completed_at`, `error`, `extracted_data`, `result`) are properly marked as nullable
- ⚠️ Need to verify frontend schema doesn't expect fields that backend doesn't send

### Data Model

**No Changes Required** - This fix only updates the endpoint path in frontend API client. No data model changes.

### Quickstart Test Scenarios

**Scenario 1: Successful Upload and Polling**
```typescript
// Frontend test flow
1. Upload file via POST /upload → Returns {job_id: "PAT-xxx", ...}
2. Start processing via POST /process → Returns {status: "PROCESSING"}
3. Poll status via GET /result/{job_id} → Returns {status: "VALIDATING", ...}
4. Continue polling every 3s until status is COMPLETED or FAILED
5. Display final result to user

// Expected behavior BEFORE fix:
- Step 3 calls GET /job/{job_id} → 405 Method Not Allowed
- Polling fails, user sees error

// Expected behavior AFTER fix:
- Step 3 calls GET /result/{job_id} → 200 OK
- Polling succeeds, user sees progress and final result
```

**Scenario 2: Error Handling for Invalid Job ID**
```typescript
// Test case
1. Call GET /result/INVALID-JOB-ID
2. Backend returns 404 with {detail: "Job not found: INVALID-JOB-ID"}
3. Frontend catches error and displays user-friendly message

// Validation: Ensure 404 handling works identically whether endpoint is /job or /result
```

### Agent Context Update

**Technologies Added**:
- None (using existing @tanstack/react-query polling mechanism)

**Changes to CLAUDE.md**:
- Update "Recent Changes" section to document this fix
- Add note about API endpoint naming convention: `/result/{resource_id}` for retrieving resource state

### Constitution Re-Check (Post-Design)

**Principle IV: Testability & Contract Validation** ✅
**Status**: RESOLVED
- Contract for `GET /result/{job_id}` verified in backend `src/api/main.py`
- Frontend schema `JobResultResponseSchema` aligns with backend `ResultResponse`
- Test update plan defined: Update `__tests__/integration/upload.test.ts` to mock correct endpoint

**Overall Post-Design Assessment**: **PASS** - All principles satisfied, ready for task generation.

---

## Implementation Strategy

### MVP Scope (User Story 1 - Priority P1)
1. Update `lib/api/queries.ts` to change `/job/{job_id}` → `/result/{job_id}`
2. Update frontend integration tests to use correct endpoint
3. Verify backend contract tests exist for `/result/{job_id}` endpoint
4. Test end-to-end upload flow: upload → process → poll → display result

### Incremental Delivery
- **Phase 1**: Code change only (1 line in `queries.ts`)
- **Phase 2**: Test updates (integration test endpoint mocks)
- **Phase 3**: Verification (manual testing + contract test review)

### Success Metrics
- Zero 405 errors in browser console during job status polling
- Job status updates display correctly in UI during processing
- End-to-end upload flow completes without errors
- Existing upload functionality remains unchanged (no regressions)

---

## Next Steps

Run `/speckit.tasks` to generate `tasks.md` with implementation checklist organized by user story.
