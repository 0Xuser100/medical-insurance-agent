# Tasks: Next.js Prescription Validation UI

**Feature Branch**: `001-prescription-ui`
**Input**: Design documents from `/specs/001-prescription-ui/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/frontend-api-contract.md, research.md, quickstart.md

**Tests**: Tests are NOT included in this task list per specification (no explicit TDD requirement in spec.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the new Next.js frontend

- [ ] T001 Create new Next.js 15.5 project with TypeScript in medical-insurance-frontend/ directory
- [ ] T002 Initialize package.json with dependencies from plan.md (Next.js 15.5, React 19, TypeScript 5.7)
- [ ] T003 [P] Configure TypeScript with strict mode in medical-insurance-frontend/tsconfig.json
- [ ] T004 [P] Configure ESLint with Next.js rules in medical-insurance-frontend/.eslintrc.json
- [ ] T005 [P] Setup Prettier with Tailwind plugin in medical-insurance-frontend/.prettierrc
- [ ] T006 Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
- [ ] T007 Create .gitignore for Next.js project (node_modules, .next, .env.local)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Install and configure Tailwind CSS 3.4 in medical-insurance-frontend/tailwind.config.ts
- [ ] T009 [P] Install tailwindcss-rtl plugin for bilingual RTL support
- [ ] T010 [P] Create globals.css with Tailwind imports in medical-insurance-frontend/styles/globals.css
- [ ] T011 Setup next-intl 4.8.2 middleware in medical-insurance-frontend/middleware.ts for locale detection
- [ ] T012 [P] Create root layout with RTL support in medical-insurance-frontend/app/[locale]/layout.tsx
- [ ] T013 [P] Create English translations file in medical-insurance-frontend/messages/en.json
- [ ] T014 [P] Create Arabic translations file in medical-insurance-frontend/messages/ar.json
- [ ] T015 Setup TanStack Query provider in medical-insurance-frontend/components/providers/QueryProvider.tsx
- [ ] T016 [P] Create Zustand language store in medical-insurance-frontend/lib/stores/useLanguageStore.ts
- [ ] T017 Create Zod schemas file with all types from data-model.md in medical-insurance-frontend/lib/schemas/validation.ts
- [ ] T018 [P] Create API client wrapper with error handling in medical-insurance-frontend/lib/api/client.ts
- [ ] T019 [P] Create utility functions (cn, formatters, validate) in medical-insurance-frontend/lib/utils/
- [ ] T020 Setup Shadcn/ui base components (button, card, badge) in medical-insurance-frontend/components/ui/
- [ ] T021 [P] Create Header component with language switcher placeholder in medical-insurance-frontend/components/features/layout/Header.tsx
- [ ] T022 [P] Create Footer component in medical-insurance-frontend/components/features/layout/Footer.tsx
- [ ] T023 Create error boundary in medical-insurance-frontend/app/[locale]/error.tsx
- [ ] T024 [P] Create 404 page in medical-insurance-frontend/app/[locale]/not-found.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Validation Results (Priority: P1) 🎯 MVP

**Goal**: Display prescription validation results with medication cards, bilingual reasons, status badges, and patient information

**Independent Test**: Provide mock validation result JSON (from response_1770464783096.json), navigate to results page, verify all sections render with proper badges and bilingual text

### Implementation for User Story 1

- [ ] T025 [P] [US1] Create StatusBadge component with color-coded badges in medical-insurance-frontend/components/features/prescription/StatusBadge.tsx
- [ ] T026 [P] [US1] Create PatientHeader component to display patient info in medical-insurance-frontend/components/features/prescription/PatientHeader.tsx
- [ ] T027 [P] [US1] Create MedicationCard component for single medication display in medical-insurance-frontend/components/features/prescription/MedicationCard.tsx
- [ ] T028 [US1] Create ResultCard component that maps line_items to MedicationCards in medical-insurance-frontend/components/features/prescription/ResultCard.tsx (depends on T025, T027)
- [ ] T029 [US1] Create TanStack Query hook for fetching job results in medical-insurance-frontend/lib/api/queries.ts
- [ ] T030 [US1] Create results page with SSR at medical-insurance-frontend/app/[locale]/prescriptions/[jobId]/page.tsx (depends on T026, T028, T029)
- [ ] T031 [P] [US1] Create loading skeleton in medical-insurance-frontend/app/[locale]/prescriptions/[jobId]/loading.tsx
- [ ] T032 [US1] Add transaction ID and timestamp display to results page
- [ ] T033 [US1] Implement bilingual reason display (reason_en/reason_ar) based on selected locale
- [ ] T034 [US1] Add confidence score and medication count display to results page
- [ ] T035 [US1] Display extracted diagnosis info with ICD code when available
- [ ] T036 [US1] Display lab analyses with validation status
- [ ] T037 [US1] Display provider information (name, facility) when available

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently with mock data

---

## Phase 4: User Story 2 - Upload Prescription (Priority: P2)

**Goal**: Enable prescription file upload with drag-and-drop, client-side validation, and bilingual error messages

**Independent Test**: Upload valid prescription file, receive job_id, verify upload confirmation without needing full validation pipeline

### Implementation for User Story 2

- [ ] T038 [P] [US2] Create file upload validation hook with Zod in medical-insurance-frontend/hooks/useFileUpload.ts
- [ ] T039 [P] [US2] Create UploadProgress component in medical-insurance-frontend/components/features/upload/UploadProgress.tsx
- [ ] T040 [US2] Create FileUploader component with react-dropzone in medical-insurance-frontend/components/features/upload/FileUploader.tsx (depends on T038)
- [ ] T041 [US2] Create upload mutation hook with TanStack Query in medical-insurance-frontend/lib/api/mutations.ts
- [ ] T042 [US2] Create upload page at medical-insurance-frontend/app/[locale]/page.tsx (depends on T040, T041)
- [ ] T043 [US2] Implement client-side file type validation (JPEG, PNG, GIF, WebP, TIFF, PDF)
- [ ] T044 [US2] Implement file size validation (max 10MB) with bilingual error messages
- [ ] T045 [US2] Add loading indicator during upload
- [ ] T046 [US2] Implement automatic redirect to status page after successful upload
- [ ] T047 [US2] Add process API call trigger after upload completion

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Track Job Status (Priority: P3)

**Goal**: Real-time job status polling with progress indicators and auto-redirect on completion

**Independent Test**: Poll mock job endpoint returning different status values, verify UI updates correctly for each status

### Implementation for User Story 3

- [ ] T048 [P] [US3] Create polling hook with auto-refetch in medical-insurance-frontend/hooks/usePrescriptionPolling.ts
- [ ] T049 [P] [US3] Create status progress indicator component in medical-insurance-frontend/components/features/prescription/StatusProgress.tsx
- [ ] T050 [US3] Create status page at medical-insurance-frontend/app/[locale]/prescriptions/status/page.tsx (depends on T048, T049)
- [ ] T051 [US3] Implement 2-second polling interval during EXTRACTING/VALIDATING states
- [ ] T052 [US3] Implement auto-stop polling on COMPLETED/FAILED status
- [ ] T053 [US3] Implement auto-redirect to results page on COMPLETED status
- [ ] T054 [US3] Display error message with retry button on FAILED status
- [ ] T055 [US3] Add job_id persistence in URL for resumable status tracking
- [ ] T056 [US3] Display appropriate progress messages for each status (EXTRACTING, VALIDATING)

**Checkpoint**: All core user stories (P1-P3) should now be independently functional

---

## Phase 6: User Story 4 - View Original Prescription (Priority: P4)

**Goal**: PDF/image viewer modal for original prescription verification

**Independent Test**: Click "View Original Prescription" button, verify image/PDF modal displays correctly

### Implementation for User Story 4

- [ ] T057 [US4] Install @react-pdf-viewer/core 1.17.0 dependency
- [ ] T058 [P] [US4] Create PDFViewer component with Web Workers in medical-insurance-frontend/components/features/prescription/PDFViewer.tsx
- [ ] T059 [P] [US4] Create ImageViewer component with zoom in medical-insurance-frontend/components/features/prescription/ImageViewer.tsx
- [ ] T060 [US4] Add "View Original Prescription" button to results page
- [ ] T061 [US4] Implement modal dialog for PDF/image display using Radix UI Dialog
- [ ] T062 [US4] Add zoom controls for PDF viewer
- [ ] T063 [US4] Add zoom controls for image viewer
- [ ] T064 [US4] Implement close modal functionality with keyboard support (Escape key)

**Checkpoint**: Original prescription viewing feature complete and independently testable

---

## Phase 7: User Story 5 - Bilingual Interface Support (Priority: P5)

**Goal**: Complete bilingual support with language toggle, RTL layout, and locale persistence

**Independent Test**: Toggle language, verify all UI elements switch languages correctly with proper text direction

### Implementation for User Story 5

- [ ] T065 [P] [US5] Create LanguageSwitcher component in medical-insurance-frontend/components/features/layout/LanguageSwitcher.tsx
- [ ] T066 [US5] Integrate LanguageSwitcher into Header component
- [ ] T067 [P] [US5] Add all upload page translations to en.json and ar.json
- [ ] T068 [P] [US5] Add all results page translations to en.json and ar.json
- [ ] T069 [P] [US5] Add all status page translations to en.json and ar.json
- [ ] T070 [P] [US5] Add all error message translations to en.json and ar.json
- [ ] T071 [US5] Implement language preference persistence in localStorage via Zustand
- [ ] T072 [US5] Test RTL layout rendering for Arabic (verify alignment, text direction)
- [ ] T073 [US5] Verify bilingual reason display uses correct locale (reason_en vs reason_ar)
- [ ] T074 [US5] Add Arabic font loading (Tajawal) in medical-insurance-frontend/app/[locale]/layout.tsx

**Checkpoint**: All user stories should now be independently functional with full bilingual support

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T075 [P] Configure Vitest with jsdom environment in medical-insurance-frontend/vitest.config.ts
- [ ] T076 [P] Configure Playwright with browser settings in medical-insurance-frontend/playwright.config.ts
- [ ] T077 [P] Setup MSW (Mock Service Worker) handlers in medical-insurance-frontend/tests/integration/api/handlers.ts
- [ ] T078 [P] Add responsive design utilities to Tailwind config for mobile-first (360px+ viewports)
- [ ] T079 [P] Implement WCAG 2.1 AA color contrast in Tailwind color palette
- [ ] T080 [P] Add focus indicators for keyboard navigation (2px outline)
- [ ] T081 [P] Add aria-labels to all interactive elements for screen readers
- [ ] T082 [P] Implement error boundary bilingual error messages
- [ ] T083 [P] Add loading states for all async operations
- [ ] T084 [P] Optimize bundle size with dynamic imports for PDF.js
- [ ] T085 [P] Add Lighthouse performance optimizations (code splitting, image optimization)
- [ ] T086 Create production build configuration in medical-insurance-frontend/next.config.ts
- [ ] T087 [P] Add environment variable validation with Zod
- [ ] T088 [P] Create deployment documentation for Vercel in medical-insurance-frontend/README.md
- [ ] T089 Run accessibility audit with axe-core (manual verification step)
- [ ] T090 Run quickstart.md validation (manual verification step)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion - Can start in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion - Can start in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational phase completion - Can start in parallel with other stories
- **User Story 5 (Phase 7)**: Depends on Foundational phase completion - Can start in parallel with other stories
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ MVP READY
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of other stories
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Cross-cutting concern, can be developed in parallel

### Within Each User Story

**User Story 1 (View Results)**:
- StatusBadge, PatientHeader, MedicationCard can be built in parallel [P]
- ResultCard depends on StatusBadge + MedicationCard
- Results page depends on all components + Query hook

**User Story 2 (Upload)**:
- File validation hook and UploadProgress can be built in parallel [P]
- FileUploader depends on validation hook
- Upload page depends on FileUploader + mutation hook

**User Story 3 (Status Tracking)**:
- Polling hook and StatusProgress can be built in parallel [P]
- Status page depends on both components

**User Story 4 (PDF Viewer)**:
- PDFViewer and ImageViewer can be built in parallel [P]
- Modal integration depends on both viewers

**User Story 5 (Bilingual)**:
- LanguageSwitcher and all translation files can be worked on in parallel [P]
- RTL testing and font loading can be done in parallel

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All Foundational tasks marked [P] can run in parallel (T009, T010, T012-T014, T016, T018-T020, T021-T022, T024)
- Once Foundational phase completes, all 5 user stories can start in parallel (if team capacity allows)
- Within each story, tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parallel components for User Story 1 together:
Task T025: "Create StatusBadge component in medical-insurance-frontend/components/features/prescription/StatusBadge.tsx"
Task T026: "Create PatientHeader component in medical-insurance-frontend/components/features/prescription/PatientHeader.tsx"
Task T027: "Create MedicationCard component in medical-insurance-frontend/components/features/prescription/MedicationCard.tsx"

# After T025 and T027 complete, launch:
Task T028: "Create ResultCard component in medical-insurance-frontend/components/features/prescription/ResultCard.tsx"

# In parallel with T028:
Task T029: "Create TanStack Query hook in medical-insurance-frontend/lib/api/queries.ts"
Task T031: "Create loading skeleton in medical-insurance-frontend/app/[locale]/prescriptions/[jobId]/loading.tsx"

# After T026, T028, T029 complete:
Task T030: "Create results page in medical-insurance-frontend/app/[locale]/prescriptions/[jobId]/page.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T024) - **CRITICAL** - blocks all stories
3. Complete Phase 3: User Story 1 (T025-T037)
4. **STOP and VALIDATE**: Test User Story 1 independently with mock data
5. Deploy/demo if ready

**MVP Deliverable**: Healthcare admins can view prescription validation results with medication cards, bilingual reasons, status badges, and patient information.

### Incremental Delivery

1. **Complete Setup + Foundational** → Foundation ready
2. **Add User Story 1 (T025-T037)** → Test independently → Deploy/Demo (MVP!)
3. **Add User Story 2 (T038-T047)** → Test independently → Deploy/Demo (Upload capability)
4. **Add User Story 3 (T048-T056)** → Test independently → Deploy/Demo (Real-time status)
5. **Add User Story 4 (T057-T064)** → Test independently → Deploy/Demo (PDF viewing)
6. **Add User Story 5 (T065-T074)** → Test independently → Deploy/Demo (Full bilingual)
7. **Polish (T075-T090)** → Final production optimizations

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T024)
2. **Once Foundational is done**:
   - Developer A: User Story 1 (T025-T037) - MVP
   - Developer B: User Story 2 (T038-T047) - Upload
   - Developer C: User Story 5 (T065-T074) - Bilingual (cross-cutting)
3. **After core stories complete**:
   - Developer D: User Story 3 (T048-T056) - Status tracking
   - Developer E: User Story 4 (T057-T064) - PDF viewer
4. **Final sprint**: Team collaborates on Phase 8 Polish (T075-T090)

Stories complete and integrate independently.

---

## Notes

- **[P] tasks** = different files, no dependencies (can run in parallel)
- **[Story] label** = maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Stop at any checkpoint to validate story independently
- Commit after each task or logical group
- **Tests NOT included**: No test tasks in this list per spec (no TDD requirement stated)
- If tests needed later: Add contract tests before implementation, integration tests after completion
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

**Total Tasks**: 90
- Phase 1 (Setup): 7 tasks
- Phase 2 (Foundational): 17 tasks (BLOCKING - must complete first)
- Phase 3 (User Story 1 - P1 MVP): 13 tasks
- Phase 4 (User Story 2 - P2): 10 tasks
- Phase 5 (User Story 3 - P3): 9 tasks
- Phase 6 (User Story 4 - P4): 8 tasks
- Phase 7 (User Story 5 - P5): 10 tasks
- Phase 8 (Polish): 16 tasks

**Parallel Opportunities**: 41 tasks marked [P] can run in parallel
**Independent Stories**: All 5 user stories can be developed in parallel after Foundational phase
**MVP Scope**: User Story 1 (13 tasks) + Setup (7 tasks) + Foundational (17 tasks) = 37 tasks for MVP

**Suggested MVP Timeline**:
- Week 1: Setup + Foundational (T001-T024)
- Week 2: User Story 1 (T025-T037)
- Week 3: Validation, testing, MVP demo

**Full Feature Timeline** (single developer):
- Week 1-2: MVP (37 tasks)
- Week 3: User Story 2 + 3 (19 tasks)
- Week 4: User Story 4 + 5 (18 tasks)
- Week 5: Polish + Testing (16 tasks)

**Full Feature Timeline** (3 developers, parallel):
- Week 1: Setup + Foundational (everyone)
- Week 2: US1 (Dev A) + US2 (Dev B) + US5 (Dev C) in parallel
- Week 3: US3 (Dev A) + US4 (Dev B) + Polish start (Dev C)
- Week 4: Polish + Testing (everyone)
