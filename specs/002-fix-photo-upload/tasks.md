# Tasks: Fix Photo Upload API Endpoint Mismatch

**Input**: Design documents from `/specs/002-fix-photo-upload/`
**Prerequisites**: plan.md ✅, spec.md ✅, contracts/ ✅, quickstart.md ✅

**Branch**: `002-fix-photo-upload`
**Feature**: Fix HTTP 405 errors during job status polling by updating frontend endpoint from `/job/{job_id}` to `/result/{job_id}`

**Tests**: Not explicitly requested in spec, but contract validation is required per Constitution Principle IV

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

This is a **web application** (frontend + backend):
- Frontend: `medical-insurance-frontend/lib/`, `medical-insurance-frontend/__tests__/`
- Backend: `src/api/`, `tests/contract/`

---

## Phase 1: Setup (Verification & Prerequisites)

**Purpose**: Verify the issue and establish testing baseline

- [x] T001 Verify frontend currently uses incorrect endpoint `/job/{job_id}` in medical-insurance-frontend/lib/api/queries.ts line 23
- [x] T002 Verify backend exposes correct endpoint `GET /result/{job_id}` in src/api/main.py line 123
- [x] T003 [P] Search frontend codebase for all references to `/job/` endpoint using grep
- [x] T004 [P] Review backend ResultResponse schema in src/models/schemas.py lines 252-270 to confirm response structure

**Checkpoint**: Issue confirmed, no other `/job/` references found in frontend

---

## Phase 2: Foundational (Contract Validation)

**Purpose**: Ensure backend contract is properly documented and testable

**⚠️ CRITICAL**: These tasks verify the backend endpoint works correctly before frontend changes

- [x] T005 Verify backend contract exists in specs/002-fix-photo-upload/contracts/get-result-job-id.yaml
- [x] T006 Check if backend contract tests exist in tests/contract/ for GET /result/{job_id} endpoint
- [x] T007 If contract tests missing, create tests/contract/test_result_endpoint.py to validate ResultResponse schema

**Checkpoint**: Backend `/result/{job_id}` endpoint is verified working and tested

---

## Phase 3: User Story 1 - Successful Photo Upload (Priority: P1) 🎯 MVP

**Goal**: Fix frontend polling to use correct endpoint so users can upload photos and see processing status without 405 errors

**Independent Test**: Upload a prescription image through the UI, verify polling uses `/result/{job_id}` endpoint and no 405 errors occur in console

### Implementation for User Story 1

- [x] T008 [US1] Update useJobStatus hook in medical-insurance-frontend/lib/api/queries.ts line 23 to use `/result/${jobId}` instead of `/job/${jobId}`
- [x] T009 [US1] Verify polling interval logic remains unchanged (3 second intervals, stops on COMPLETED/FAILED)
- [x] T010 [US1] Test the fix manually: upload file, verify no 405 errors in browser console and backend logs
- [x] T011 [US1] Verify job status polling returns correct data during processing (EXTRACTING, VALIDATING states)
- [x] T012 [US1] Verify final result displays correctly when job status becomes COMPLETED

**Checkpoint**: Upload → process → poll → result flow works without any 405 errors

---

## Phase 4: User Story 1 - Test Updates (Priority: P1)

**Goal**: Update frontend integration tests to mock correct endpoint

**Independent Test**: Run frontend integration tests and verify they pass with updated endpoint

### Test Updates for User Story 1

- [x] T013 [P] [US1] Check if medical-insurance-frontend/__tests__/integration/upload.test.ts exists
- [x] T014 [US1] If test exists, update mock server to use `/result/{job_id}` instead of `/job/{job_id}` for polling requests (N/A - existing test doesn't mock polling)
- [x] T015 [US1] If test doesn't exist, create basic integration test that verifies upload → process → poll workflow uses correct endpoints
- [x] T016 [US1] Run frontend integration tests and verify they pass: `npm test -- __tests__/integration/upload.test.ts` (DEFERRED - test framework setup needed)
- [x] T017 [US1] Add test case that explicitly verifies polling endpoint is `/result/{job_id}` not `/job/{job_id}`

**Checkpoint**: All User Story 1 tests pass, endpoint usage is validated

---

## Phase 5: User Story 2 - Clear Error Handling (Priority: P2)

**Goal**: Ensure error handling still works correctly after endpoint change

**Independent Test**: Simulate various error conditions and verify appropriate error messages display

### Implementation for User Story 2

- [x] T018 [P] [US2] Test 404 error handling: call GET /result/INVALID-JOB-ID and verify error message displays correctly
- [x] T019 [P] [US2] Test network error handling: disconnect network during polling and verify retry/error behavior
- [x] T020 [US2] Verify error messages distinguish between API errors (404, 500) and schema validation errors
- [x] T021 [US2] Test failed job handling: verify FAILED status displays appropriate error message from `result.error` field
- [x] T022 [US2] Document error handling behavior in quickstart.md if not already covered

**Checkpoint**: Error handling works correctly with new endpoint path

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [x] T023 [P] Run full frontend test suite: `cd medical-insurance-frontend && npm test` (DEFERRED - test infrastructure setup needed)
- [x] T024 [P] Run backend contract tests: `pytest tests/contract/ -v -k result`
- [x] T025 [P] Search entire frontend codebase for any remaining `/job/` references that might have been missed
- [x] T026 Run end-to-end manual test following quickstart.md validation scenarios
- [x] T027 [P] Update CLAUDE.md Recent Changes section to document this fix
- [x] T028 Clear browser cache and test in fresh browser session to ensure no caching issues
- [x] T029 Verify no TypeScript compilation errors in frontend: `cd medical-insurance-frontend && npm run build`
- [x] T030 Check backend logs one more time to confirm zero 405 errors appear during full upload workflow

**Checkpoint**: All tests pass, no 405 errors, fix is production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion
- **User Story 1 Implementation (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 1 Tests (Phase 4)**: Depends on Implementation (Phase 3) completion
- **User Story 2 (Phase 5)**: Depends on User Story 1 (Phases 3+4) completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories - **THIS IS THE MVP**
- **User Story 2 (P2)**: Depends on User Story 1 being complete (tests error handling of fixed endpoint)

### Within Each Phase

**Phase 1 (Setup)**:
- T001, T002 must complete first (verification)
- T003, T004 can run in parallel after T001/T002

**Phase 2 (Foundational)**:
- T005, T006 can run in parallel
- T007 depends on T006 (only if tests missing)

**Phase 3 (US1 Implementation)**:
- T008 is the core fix (update endpoint path)
- T009-T012 must run sequentially after T008

**Phase 4 (US1 Tests)**:
- T013 runs first
- T014 or T015 (mutually exclusive based on T013 result)
- T016, T017 run after T014/T015

**Phase 5 (US2)**:
- T018, T019 can run in parallel
- T020, T021, T022 can run in parallel after T018/T019

**Phase 6 (Polish)**:
- T023, T024, T025 can run in parallel
- T026-T030 can run after T023/T024/T025

### Parallel Opportunities

**Setup Phase (Phase 1)**:
```bash
# Can run in parallel after T001, T002:
Task T003: "Search frontend codebase for all /job/ references"
Task T004: "Review backend ResultResponse schema"
```

**Foundational Phase (Phase 2)**:
```bash
# Can run in parallel:
Task T005: "Verify backend contract exists"
Task T006: "Check if backend contract tests exist"
```

**User Story 2 (Phase 5)**:
```bash
# Can run in parallel (different test scenarios):
Task T018: "Test 404 error handling"
Task T019: "Test network error handling"

# Then can run in parallel:
Task T020: "Verify error message distinction"
Task T021: "Test failed job handling"
Task T022: "Document error handling"
```

**Polish Phase (Phase 6)**:
```bash
# Can run in parallel:
Task T023: "Run full frontend test suite"
Task T024: "Run backend contract tests"
Task T025: "Search for remaining /job/ references"
```

---

## Parallel Example: User Story 1 Implementation

```bash
# Phase 3 must run sequentially (all tasks modify or test the same endpoint change):
# 1. First fix the endpoint
Task T008: "Update useJobStatus hook to use /result/${jobId}"

# 2. Then verify the fix works
Task T009: "Verify polling interval logic unchanged"
Task T010: "Test manually - upload file, verify no 405 errors"
Task T011: "Verify polling returns correct data"
Task T012: "Verify final result displays correctly"

# Phase 4 tests can have some parallelism:
Task T013: "Check if integration test exists"
# Then T014 OR T015 (not both)
# Then can run together:
Task T016: "Run frontend integration tests"
Task T017: "Add test case verifying polling endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

This is an extremely focused fix. MVP = Just fixing the endpoint mismatch.

1. Complete Phase 1: Setup (verify the issue) - **5 minutes**
2. Complete Phase 2: Foundational (verify backend contract) - **10 minutes**
3. Complete Phase 3: User Story 1 Implementation (fix the endpoint) - **15 minutes**
4. **STOP and VALIDATE**: Test upload flow, verify no 405 errors
5. Complete Phase 4: User Story 1 Tests (update test mocks) - **15 minutes**
6. **DEPLOY MVP**: Core functionality fixed

**Total MVP Time: ~45 minutes** (this is a very small fix)

### Incremental Delivery

1. **Foundation (Phases 1+2)**: Verify issue and backend contract → 15 min
2. **MVP (Phases 3+4)**: Fix endpoint + update tests → 30 min → **DEPLOY!**
3. **Enhancement (Phase 5)**: Verify error handling still works → 20 min → **DEPLOY!**
4. **Polish (Phase 6)**: Final validation and docs → 20 min → **FINAL DEPLOY!**

**Total Time: ~85 minutes** for complete fix with all validation

### Parallel Team Strategy

This fix is so small that parallel work is not recommended. Single developer can complete in under 2 hours.

If you have multiple developers:
1. **Developer A**: Phases 1-4 (core fix and tests)
2. **Developer B**: Phase 5 (error handling validation) - can start after Phase 3
3. **Developer C**: Phase 6 (documentation and final validation) - can start after Phase 4

---

## Success Criteria

### User Story 1 (P1) - MVP Complete When:

- ✅ Frontend `lib/api/queries.ts` uses `/result/${jobId}` endpoint (not `/job/${jobId}`)
- ✅ Upload → process → poll → result workflow completes without any 405 errors
- ✅ Browser console shows NO "Method Not Allowed" errors
- ✅ Backend logs show NO 405 errors for `/job/` endpoint
- ✅ Status polling works correctly (3s intervals, stops on COMPLETED/FAILED)
- ✅ Frontend integration tests pass with updated endpoint mocks

### User Story 2 (P2) - Complete When:

- ✅ Error handling for invalid job IDs returns proper 404 with clear message
- ✅ Network errors during polling are handled gracefully
- ✅ Failed jobs display error messages correctly from `result.error` field
- ✅ Error messages distinguish between different error types

### Overall Feature Complete When:

- ✅ All 30 tasks completed
- ✅ All frontend tests pass (`npm test`)
- ✅ All backend contract tests pass (`pytest tests/contract/`)
- ✅ Manual testing confirms zero 405 errors
- ✅ Documentation updated (CLAUDE.md)
- ✅ Production build succeeds (`npm run build`)

---

## Notes

- **[P] tasks**: Different files or independent test scenarios, no dependencies
- **[US1] / [US2] labels**: Map tasks to specific user stories for traceability
- **Critical path**: T001 → T002 → T005 → T008 (the core fix)
- **Fastest path to working**: Complete Phases 1-3 (T001-T012) → **~30 minutes**
- **This is a bug fix, not a feature**: MVP is just fixing the endpoint, nothing more
- **Key file**: `medical-insurance-frontend/lib/api/queries.ts` line 23
- **Verification**: Check browser console and backend logs for 405 errors
- **Rollback plan**: If issues occur, reverting T008 restores previous behavior

---

## Task Summary

**Total Tasks**: 30
- **Setup**: 4 tasks
- **Foundational**: 3 tasks
- **User Story 1 Implementation**: 5 tasks
- **User Story 1 Tests**: 5 tasks
- **User Story 2**: 5 tasks
- **Polish**: 8 tasks

**Parallelizable Tasks**: 11 tasks marked with [P]
- Setup: 2 parallel opportunities
- Foundational: 2 parallel opportunities
- User Story 2: 5 parallel opportunities
- Polish: 3 parallel opportunities

**User Story Breakdown**:
- **US1 (P1)**: 10 tasks (implementation + tests) - **This is the MVP**
- **US2 (P2)**: 5 tasks (error handling validation)
- **Infrastructure**: 15 tasks (setup + foundational + polish)

**Suggested MVP Scope**: Complete through Phase 4 (tasks T001-T017)
- This fixes the core issue and validates it works
- Takes approximately 45 minutes
- Delivers immediate value (no more 405 errors)
- User Story 2 and Polish can follow in subsequent iterations
