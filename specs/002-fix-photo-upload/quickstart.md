# Quickstart: Testing the Photo Upload API Endpoint Fix

**Feature**: 002-fix-photo-upload (Fix Photo Upload API Endpoint Mismatch)
**Date**: 2026-02-07
**Purpose**: Guide for developers to test the frontend endpoint path fix (`/job/{job_id}` → `/result/{job_id}`)

---

## Overview

This guide provides step-by-step instructions for:
1. Setting up the development environment
2. Testing the endpoint fix manually
3. Running automated tests
4. Verifying no 405 errors occur during job polling

---

## Prerequisites

### Required Software
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- Docker (optional, for containerized testing)

### Required Files
Ensure these files exist before testing:
- ✅ Backend: `src/api/main.py` (GET /result/{job_id} endpoint)
- ✅ Frontend: `medical-insurance-frontend/lib/api/queries.ts` (after fix - using /result/ not /job/)
- ✅ Frontend: `medical-insurance-frontend/components/features/upload/UploadZone.tsx`

---

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to project root
cd D:\medical-insurance-agent

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn src.api.main:app --reload --port 8000
```

**Verify**: Backend should be running at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd medical-insurance-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Verify**: Frontend should be running at `http://localhost:3000`

---

## Manual Testing

### Test Case 1: Successful Upload and Polling

**Steps**:
1. Open browser to `http://localhost:3000`
2. Open DevTools (F12) → Network tab
3. Navigate to the upload page
4. Select or drag a valid image file (PNG/JPG, <10MB)
5. Click upload or drop the file
6. Observe Network tab requests during processing

**Expected Network Requests**:
```
POST /upload              → 200 OK
POST /process             → 200 OK
GET /result/{job_id}      → 200 OK  (polling, repeats every 3s)
GET /result/{job_id}      → 200 OK
GET /result/{job_id}      → 200 OK  (final result)
```

**Expected Result**:
- ✅ Upload completes successfully
- ✅ Processing starts automatically
- ✅ Status polling uses `/result/{job_id}` endpoint (NOT `/job/{job_id}`)
- ✅ No HTTP 405 "Method Not Allowed" errors
- ✅ Status updates appear in UI (EXTRACTING → VALIDATING → COMPLETED)
- ✅ Final result displays correctly

**Before Fix** (What was broken):
- ❌ Frontend polls using `GET /job/{job_id}`
- ❌ Backend returns HTTP 405 "Method Not Allowed"
- ❌ Console shows: `INFO: 127.0.0.1:XXXX - "GET /job/PAT-xxx HTTP/1.1" 405 Method Not Allowed`
- ❌ Upload succeeds but polling fails, so user sees processing status errors

**After Fix**:
- ✅ Frontend polls using `GET /result/{job_id}`
- ✅ Backend returns HTTP 200 OK
- ✅ No 405 errors in console
- ✅ Status polling works correctly

### Test Case 2: Job Status Polling Inspection

**Steps**:
1. Open browser DevTools (F12) → Network tab
2. Upload a file
3. Find the repeating `GET /result/{job_id}` requests (they appear every 3 seconds)
4. Click on one request and view the Response

**Expected Response** (processing):
```json
{
  "job_id": "PAT-0b1f01e6dc5f",
  "status": "VALIDATING",
  "created_at": "2026-02-07T18:37:55.000Z",
  "started_at": "2026-02-07T18:37:56.000Z",
  "completed_at": null,
  "error": "Processing... Current stage: VALIDATING",
  "extracted_data": null,
  "result": null
}
```

**Expected Response** (completed):
```json
{
  "job_id": "PAT-0b1f01e6dc5f",
  "status": "COMPLETED",
  "created_at": "2026-02-07T18:37:55.000Z",
  "started_at": "2026-02-07T18:37:56.000Z",
  "completed_at": "2026-02-07T18:38:18.000Z",
  "error": null,
  "extracted_data": {...},
  "result": {...}
}
```

**Verification**:
- ✅ All requests use `/result/{job_id}` path (NOT `/job/{job_id}`)
- ✅ HTTP status is 200 OK (NOT 405 Method Not Allowed)
- ✅ Response includes all expected fields
- ✅ Polling stops when status is "COMPLETED" or "FAILED"

### Test Case 3: Verify No Endpoint Mismatch

**Steps**:
1. Open browser DevTools (F12) → Console tab
2. Upload a file
3. Watch for any error messages during processing

**Expected Console Output**:
- ✅ NO errors like: `GET http://localhost:8000/job/PAT-xxx 405 (Method Not Allowed)`
- ✅ NO fetch errors or API call failures
- ✅ Only successful requests logged

**Backend Console Verification**:
```bash
# Check backend logs - should see ONLY /result/ requests, NO /job/ requests
INFO:     127.0.0.1:XXXX - "POST /upload HTTP/1.1" 200 OK
INFO:     127.0.0.1:XXXX - "POST /process HTTP/1.1" 200 OK
INFO:     127.0.0.1:XXXX - "GET /result/PAT-xxx HTTP/1.1" 200 OK  ✅
INFO:     127.0.0.1:XXXX - "GET /result/PAT-xxx HTTP/1.1" 200 OK  ✅

# Should NOT see:
# INFO:     127.0.0.1:XXXX - "GET /job/PAT-xxx HTTP/1.1" 405 Method Not Allowed  ❌
```

---

## Automated Testing

### Backend Contract Tests

```bash
# Navigate to project root
cd D:\medical-insurance-agent

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run contract tests for /result endpoint
pytest tests/contract/ -v -k "result"

# Expected output:
# tests/contract/test_api_contracts.py::test_get_result_endpoint_schema_valid PASSED
# tests/contract/test_api_contracts.py::test_get_result_endpoint_response_structure PASSED
# tests/contract/test_api_contracts.py::test_get_result_endpoint_404_on_invalid_job PASSED
```

**What this tests**:
- ✅ Backend `/result/{job_id}` endpoint exists and responds correctly
- ✅ Response schema matches contract specification
- ✅ 404 handling works for invalid job IDs

### Frontend Query Tests

```bash
# Navigate to frontend
cd medical-insurance-frontend

# Run API query tests
npm test -- lib/api/queries.test.ts

# Expected output:
# PASS lib/api/queries.test.ts
#   useJobStatus hook
#     ✓ uses correct endpoint /result/{job_id} (5ms)
#     ✓ polls every 3 seconds while processing (150ms)
#     ✓ stops polling when status is COMPLETED (120ms)
#     ✓ stops polling when status is FAILED (110ms)
```

**What this tests**:
- ✅ `useJobStatus` hook calls `/result/{job_id}` (NOT `/job/{job_id}`)
- ✅ Polling interval works correctly
- ✅ Polling stops when job completes or fails

### Frontend Integration Tests

```bash
# Navigate to frontend
cd medical-insurance-frontend

# Run integration tests
npm test -- __tests__/integration/upload.test.ts

# Expected output:
# PASS __tests__/integration/upload.test.ts
#   Upload Integration
#     ✓ successfully uploads file and starts processing (150ms)
#     ✓ polls job status using /result endpoint (200ms)
#     ✓ displays final result when processing completes (180ms)
#     ✓ handles processing errors gracefully (80ms)
```

**What this tests**:
- ✅ End-to-end upload → process → poll → result flow works
- ✅ Status polling uses correct endpoint
- ✅ UI updates correctly during processing phases

### Run All Tests

```bash
# Backend
cd D:\medical-insurance-agent
.venv\Scripts\activate
pytest tests/ -v

# Frontend
cd medical-insurance-frontend
npm test
```

---

## Debugging Guide

### Issue: Still Seeing 405 Errors After Fix

**Symptoms**:
- Console shows: `GET /job/PAT-xxx 405 (Method Not Allowed)`
- Backend logs show 405 errors
- Status polling fails

**Diagnosis**:
1. Check if frontend code was actually updated:
   ```bash
   cd medical-insurance-frontend
   grep -n "/job/" lib/api/queries.ts
   ```
   Should return NO matches (or only in comments)
   Line 23 should read: `const data = await apiFetch(\`/result/${jobId}\`);`

2. Check if frontend was restarted after code change:
   ```bash
   # Kill and restart Next.js dev server
   # Ctrl+C, then:
   npm run dev
   ```

3. Clear browser cache and hard reload (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Polling Doesn't Stop After Completion

**Symptoms**:
- Requests to `/result/{job_id}` continue indefinitely
- Status shows "COMPLETED" but polling doesn't stop

**Diagnosis**:
1. Check frontend polling logic:
   ```bash
   cd medical-insurance-frontend
   cat lib/api/queries.ts | grep -A 5 "refetchInterval"
   ```
   Should include logic to return `false` when status is "COMPLETED" or "FAILED"

2. Check backend returns correct final status:
   ```bash
   # Manually test result endpoint
   curl http://localhost:8000/result/PAT-xxx | jq '.status'
   ```
   Should return "COMPLETED" or "FAILED", not "PROCESSING"

### Issue: Tests Failing

**Symptoms**:
- Contract tests fail
- Integration tests fail

**Diagnosis**:
1. Check test files exist:
   ```bash
   ls tests/contract/test_api_contracts.py
   ls medical-insurance-frontend/__tests__/integration/upload.test.ts
   ```

2. Install test dependencies:
   ```bash
   # Backend
   pip install pytest pytest-asyncio httpx

   # Frontend
   cd medical-insurance-frontend
   npm install --save-dev @testing-library/react @testing-library/jest-dom
   ```

3. Check if tests are mocking the correct endpoint:
   ```bash
   cd medical-insurance-frontend
   grep -n "/job/" __tests__/**/*.ts
   ```
   Should return NO matches - all tests should use `/result/` for polling

---

## Verification Checklist

Before considering the fix complete, verify:

### Functionality
- [ ] Can upload valid image files (PNG, JPG, JPEG)
- [ ] Processing starts automatically after upload
- [ ] Job status polling uses `/result/{job_id}` endpoint
- [ ] NO HTTP 405 errors in console or backend logs
- [ ] Status updates appear during processing (EXTRACTING, VALIDATING, etc.)
- [ ] Final result displays correctly when COMPLETED

### Testing
- [ ] Backend contract tests pass for `/result/{job_id}` endpoint
- [ ] Frontend query tests pass for `useJobStatus` hook
- [ ] Frontend integration tests pass for end-to-end upload flow
- [ ] Manual testing confirms no 405 errors occur

### Code Quality
- [ ] Frontend `lib/api/queries.ts` uses `/result/` not `/job/`
- [ ] No references to `/job/{job_id}` in frontend codebase
- [ ] No TypeScript errors in queries.ts
- [ ] Contract documentation includes `/result/{job_id}` specification

### User Experience
- [ ] Status polling is seamless (no visible errors)
- [ ] Processing status updates in real-time
- [ ] Final result displays within 2s of completion
- [ ] No confusing error messages during normal operation

---

## Common Commands Reference

### Backend
```bash
# Start backend
uvicorn src.api.main:app --reload --port 8000

# Run backend tests
pytest tests/ -v

# Check schema definition
cat src/models/schemas.py | grep -A 20 "class UploadResponse"
```

### Frontend
```bash
# Start frontend
cd medical-insurance-frontend && npm run dev

# Run frontend tests
npm test

# Run specific test file
npm test -- lib/api/queries.test.ts

# Check queries definition
cat lib/api/queries.ts | grep -A 5 "useJobStatus"

# Verify no /job/ references
grep -r "/job/" lib/ --include="*.ts" --include="*.tsx"

# Build for production
npm run build
```

### Full System Test
```bash
# Terminal 1: Backend
cd D:\medical-insurance-agent
.venv\Scripts\activate
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd D:\medical-insurance-agent\medical-insurance-frontend
npm run dev

# Terminal 3: Run tests
cd D:\medical-insurance-agent
pytest tests/contract/ -v

cd medical-insurance-frontend
npm test
```

---

## Success Criteria

✅ **Fix is complete when**:
1. All automated tests pass (backend + frontend)
2. Job status polling uses `/result/{job_id}` endpoint
3. No HTTP 405 errors in browser console or backend logs
4. Contract tests confirm `/result/{job_id}` endpoint works correctly
5. End-to-end upload → process → poll → result flow completes successfully

---

## Next Steps After Testing

1. ✅ All tests pass → Ready to commit
2. ✅ Manual testing confirms fix → Ready for PR
3. ✅ Code review approved → Ready to merge
4. ✅ Deployed to staging → Ready for QA testing
5. ✅ QA approved → Ready for production

---

## Support

**Issues?**
- Check the [Debugging Guide](#debugging-guide) above
- Review the [API Contract Specification](./contracts/get-result-job-id.yaml)
- Verify backend endpoint at `src/api/main.py` line 123

**Questions?**
- Review [Implementation Plan](./plan.md) for root cause analysis
- Check backend logs for actual requests being made

---

**Last Updated**: 2026-02-07
**Status**: Ready for Phase 2 (Implementation)
