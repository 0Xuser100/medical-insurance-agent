# Implementation Plan: Next.js Prescription Validation UI

**Branch**: `001-prescription-ui` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-prescription-ui/spec.md`

---

## Summary

Build a production-ready Next.js 15 frontend for the Medical Insurance Validation API that displays prescription validation results with bilingual support (EN/AR), real-time job status polling, and WCAG 2.1 AA accessibility compliance. The UI enables healthcare administrators to upload prescriptions, track async processing, and review AI-generated validation decisions with clear visual indicators and bilingual explanations.

**Key Features**:
- File upload with drag-and-drop (JPEG, PNG, PDF, max 10MB)
- Real-time job status polling (UPLOADED → EXTRACTING → VALIDATING → COMPLETED)
- Medication validation cards with color-coded badges (✓ Approved, ❌ Rejected)
- Bilingual interface (English/Arabic with RTL layout)
- PDF viewer for original prescription review
- Mobile-first responsive design (360px+ viewports)
- WCAG 2.1 AA accessibility (May 2026 HHS compliance deadline)

---

## Technical Context

**Language/Version**: TypeScript 5.7 with Next.js 15.5 (App Router)
**Primary Dependencies**:
- Frontend: React 19, Next.js 15.5, next-intl 4.8.2, TanStack Query 5.90.20, Zustand 5.0.6
- Styling: Tailwind CSS 3.4, tailwindcss-rtl, Shadcn/ui (Radix UI primitives)
- Validation: Zod 3.24.1, React Hook Form 7.54.2
- File Handling: react-dropzone 14.3.5, @react-pdf-viewer/core 1.17.0
- Testing: Vitest 3.1.0, Playwright 1.50.0, @testing-library/react 16.1.0

**Storage**: No database (frontend-only); backend API handles all persistence
**Testing**: Vitest for unit/component tests, Playwright for E2E, axe-core for WCAG audits
**Target Platform**: Web (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+), mobile-responsive
**Project Type**: Web application (frontend only, connects to existing FastAPI backend)
**Performance Goals**:
- LCP <2.5s (Largest Contentful Paint)
- FID <100ms (First Input Delay)
- CLS <0.1 (Cumulative Layout Shift)
- Bundle size <200KB (excluding PDF.js worker)

**Constraints**:
- Must poll backend every 2s during processing (no WebSockets in MVP)
- Backend API already built (no backend modifications)
- Authentication/authorization out of scope (handled separately)
- WCAG 2.1 AA compliance required by May 11, 2026 (HHS deadline)
- Bilingual support is mandatory (Constitution Principle II)

**Scale/Scope**:
- Single-page application (5 routes: home, upload, status, results, 404)
- Expected: 100-500 concurrent users
- File uploads: 10-50 per hour
- Average job processing time: 20-50 seconds

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle II: Bilingual & Accessibility by Default
- **Requirement**: Every user-facing message must include English and Arabic
- **Implementation**:
  - next-intl 4.8.2 with locale-based routing (`/[locale]/`)
  - Automatic RTL layout switching for Arabic (`dir="rtl"`)
  - Translation files: `messages/en.json`, `messages/ar.json`
  - Display `reason_en` and `reason_ar` from API responses
- **Status**: ✅ PASS - Full bilingual support with RTL

### ✅ Principle III: Async-First Architecture
- **Requirement**: All I/O-bound operations must use async/await patterns
- **Implementation**:
  - TanStack Query for async API state (auto-polling, caching)
  - React 19 Suspense for streaming SSR
  - Non-blocking file uploads with FormData
- **Status**: ✅ PASS - Fully async architecture

### ✅ Principle IV: Testability & Contract Validation
- **Requirement**: Contract tests before implementation, mock external dependencies
- **Implementation**:
  - Zod schemas mirror backend Pydantic models (`data-model.md`)
  - API contract defined (`contracts/frontend-api-contract.md`)
  - MSW (Mock Service Worker) for API mocking in tests
  - Vitest component tests + Playwright E2E tests
- **Status**: ✅ PASS - Test-first approach with contract validation

### ✅ Principle V: Observability & Auditability
- **Requirement**: Display transaction IDs, timestamps, audit trails
- **Implementation**:
  - Transaction ID displayed prominently on results page
  - ISO 8601 timestamps for job lifecycle (created_at, started_at, completed_at)
  - Error boundaries with actionable error messages
- **Status**: ✅ PASS - Full audit trail visibility

### ⚠️ Additional Considerations
- **Data Privacy** (Constitution Security): Patient data never logged in browser console (production mode)
- **Error Handling**: Bilingual error messages, no stack traces exposed
- **Accessibility**: WCAG 2.1 AA compliance via Radix UI + axe-core testing

**Overall**: ✅ ALL GATES PASSED - No constitution violations

---

## Project Structure

### Documentation (this feature)

```text
specs/001-prescription-ui/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (TypeScript types + Zod schemas)
├── quickstart.md        # Phase 1 output (developer setup guide)
├── contracts/           # Phase 1 output (API contract)
│   └── frontend-api-contract.md
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (repository root)

**Structure Decision**: Web application (frontend as separate project from backend)

```text
medical-insurance-agent/          # Backend (existing)
└── src/                          # FastAPI backend

medical-insurance-frontend/       # Frontend (new project)
├── app/[locale]/                 # Next.js App Router with i18n
│   ├── layout.tsx                # Root layout (RTL support)
│   ├── page.tsx                  # Homepage (file upload)
│   ├── prescriptions/
│   │   ├── page.tsx              # Job list view
│   │   └── [jobId]/
│   │       ├── page.tsx          # Result detail view (SSR)
│   │       ├── loading.tsx       # Suspense fallback
│   │       └── error.tsx         # Error boundary
│   ├── error.tsx                 # Global error boundary
│   └── not-found.tsx             # 404 page
│
├── components/
│   ├── ui/                       # Shadcn/ui primitives (Radix UI)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── toast.tsx
│   │   └── alert-dialog.tsx
│   ├── features/
│   │   ├── upload/
│   │   │   ├── FileUploader.tsx      # Drag-drop + validation
│   │   │   └── UploadProgress.tsx    # Upload progress bar
│   │   ├── prescription/
│   │   │   ├── ResultCard.tsx        # Medication line items
│   │   │   ├── MedicationCard.tsx    # Single medication display
│   │   │   ├── StatusBadge.tsx       # ✓/❌ badges
│   │   │   ├── PDFViewer.tsx         # Embedded PDF preview
│   │   │   └── PatientHeader.tsx     # Patient info display
│   │   └── layout/
│   │       ├── LanguageSwitcher.tsx  # EN/AR toggle
│   │       ├── Header.tsx            # App header
│   │       └── Footer.tsx            # App footer
│   └── providers/
│       ├── QueryProvider.tsx         # TanStack Query wrapper
│       └── IntlProvider.tsx          # next-intl provider
│
├── lib/
│   ├── api/
│   │   ├── client.ts                 # Fetch wrapper with error handling
│   │   ├── queries.ts                # TanStack Query hooks (GET)
│   │   └── mutations.ts              # TanStack Query mutations (POST/DELETE)
│   ├── schemas/
│   │   └── validation.ts             # Zod schemas (from data-model.md)
│   ├── stores/
│   │   └── useLanguageStore.ts       # Zustand store for locale
│   └── utils/
│       ├── cn.ts                     # clsx + tailwind-merge
│       ├── formatters.ts             # Date/time formatting
│       └── validate.ts               # API response validation utility
│
├── hooks/
│   ├── useFileUpload.ts              # File validation logic
│   ├── usePrescriptionPolling.ts     # Auto-polling hook
│   └── useRTL.ts                     # RTL direction helper
│
├── messages/                         # i18n translations
│   ├── en.json
│   └── ar.json
│
├── public/
│   ├── fonts/                        # Arabic fonts (Tajawal, Noto Sans Arabic)
│   └── icons/
│
├── styles/
│   └── globals.css                   # Tailwind imports + RTL utilities
│
├── types/
│   └── api.ts                        # TypeScript types from Zod schemas
│
├── tests/
│   ├── unit/
│   │   └── components/               # Vitest component tests
│   │       ├── StatusBadge.test.tsx
│   │       └── FileUploader.test.tsx
│   ├── integration/
│   │   └── api/                      # API mocking with MSW
│   │       └── handlers.ts
│   └── e2e/
│       ├── prescription.spec.ts      # Playwright E2E tests
│       └── accessibility.spec.ts     # WCAG 2.1 AA audit
│
├── middleware.ts                     # next-intl locale detection
├── next.config.ts                    # TypeScript config
├── tailwind.config.ts                # Tailwind + RTL plugin
├── vitest.config.ts                  # Vitest configuration
├── playwright.config.ts              # Playwright configuration
├── package.json
└── .env.local                        # Environment variables
```

---

## Phase 0: Outline & Research ✅ COMPLETED

### Research Summary

**Completed**: 2026-02-07
**Document**: [research.md](./research.md)

**Key Decisions**:
1. **Framework**: Next.js 15.5 with App Router (vs Pages Router, Remix, Vite SPA)
2. **Internationalization**: next-intl 4.8.2 (vs react-i18next, next-translate)
3. **State Management**: TanStack Query 5.90.20 + Zustand 5.0.6 (vs Redux, SWR)
4. **Styling**: Tailwind CSS 3.4 + tailwindcss-rtl (vs CSS Modules, Styled Components)
5. **Type Safety**: Zod 3.24.1 for runtime validation (vs Yup, io-ts)
6. **File Upload**: react-dropzone 14.3.5 (vs native input)
7. **PDF Viewing**: @react-pdf-viewer/core 1.17.0 (vs react-pdf, PSPDFKit)
8. **Testing**: Vitest 3.1.0 (10× faster than Jest) + Playwright 1.50.0 (vs Cypress)
9. **Accessibility**: Shadcn/ui (Radix UI primitives) + axe-core
10. **Folder Structure**: Feature-based organization with App Router

**All NEEDS CLARIFICATION items resolved** - see `research.md` for detailed rationale

---

## Phase 1: Design & Contracts ✅ COMPLETED

### 1.1 Data Model ✅

**Completed**: 2026-02-07
**Document**: [data-model.md](./data-model.md)

**Entities Defined**:
- `JobStatus` - Enum for processing state
- `Patient` - Patient demographic information
- `Provider` - Healthcare provider details
- `Diagnosis` - Primary diagnosis with ICD-10 code
- `Medication` - Medication item with dosage/frequency
- `LabAnalysis` - Laboratory test requested
- `ExtractedData` - Complete OCR extraction result
- `ValidationDetails` - Per-item validation (clinical_match, bilingual reasons)
- `LineItem` - Individual validation result (medication/lab)
- `AIValidationEngine` - Overall validation with line items
- `ValidationResult` - Complete validation result with metadata
- `JobResultResponse` - Full API response schema

**Zod Schemas**: All entities have corresponding Zod schemas for runtime validation

---

### 1.2 API Contracts ✅

**Completed**: 2026-02-07
**Document**: [contracts/frontend-api-contract.md](./contracts/frontend-api-contract.md)

**Endpoints Specified**:
1. `GET /health` - Health check
2. `POST /upload` - Upload prescription file
3. `POST /process` - Start processing job
4. `GET /result/{job_id}` - Poll job status and results
5. `DELETE /job/{job_id}` - Cancel/delete job
6. `GET /jobs?status={status}` - List all jobs with filtering

**Contract Validation**:
- Request/response schemas defined
- Error handling patterns specified
- CORS configuration documented
- Rate limiting strategy outlined
- Performance expectations set (response times, timeouts)

---

### 1.3 Quickstart Guide ✅

**Completed**: 2026-02-07
**Document**: [quickstart.md](./quickstart.md)

**Sections**:
1. Initial setup (5 min)
2. Development server (1 min)
3. Backend connection test (2 min)
4. Run tests (5 min)
5. Language testing (2 min)
6. File upload validation test
7. Job status polling test
8. Accessibility testing (3 min)
9. Common development tasks
10. Production build test
11. Troubleshooting
12. Next steps

**Setup Time**: ~15 minutes from zero to running dev server

---

### 1.4 Agent Context Update

**Status**: Ready for manual execution after this command completes

**Command**:
```bash
powershell.exe -File .specify/scripts/powershell/update-agent-context.ps1 -AgentType claude
```

**Purpose**: Update `.claude/agent-context.md` with:
- Next.js 15.5 App Router patterns
- TanStack Query polling strategies
- next-intl bilingual routing
- Tailwind RTL utilities
- Vitest + Playwright testing setup

---

## Phase 2: Constitution Re-Check ✅

*Post-design validation of constitution compliance*

### Verification Matrix

| Principle | Requirement | Implementation | Status |
|-----------|-------------|----------------|--------|
| II. Bilingual | EN/AR messages, RTL layout | next-intl + tailwindcss-rtl | ✅ PASS |
| III. Async | Non-blocking I/O | TanStack Query + React Suspense | ✅ PASS |
| IV. Testability | Contract tests, mocking | Zod schemas + MSW + Vitest | ✅ PASS |
| V. Observability | Transaction IDs, timestamps | UI displays all audit fields | ✅ PASS |

**Security & Compliance**:
- ✅ Data Privacy: No patient data in console logs (production mode)
- ✅ Error Handling: Bilingual error messages, no stack traces
- ✅ Accessibility: WCAG 2.1 AA via Radix UI + axe-core

**Final Assessment**: ✅ ALL PRINCIPLES SATISFIED

---

## Complexity Tracking

> **No constitution violations - this section is empty per template instructions**

---

## Implementation Notes

### User Story Priorities (for `/speckit.tasks`)

Tasks should be organized by user story priority from spec.md:

1. **P1: View Validation Results** (MVP - Core Value)
   - This is the most critical feature - the reason the UI exists
   - Frontend can be developed with mock API responses initially

2. **P2: Upload Prescription for Analysis**
   - Entry point to workflow
   - Can be tested independently with backend /upload endpoint

3. **P3: Track Job Status**
   - Enhances UX with real-time feedback
   - Requires polling implementation (TanStack Query refetchInterval)

4. **P4: View Original Prescription**
   - Audit/verification feature
   - Separate modal component (can be added last)

5. **P5: Bilingual Interface Support**
   - Critical for Constitution compliance but can be added as cross-cutting concern
   - Implement incrementally: language toggle → translations → RTL layout

### Critical Path

```
Phase 1: Setup
  ├── Initialize Next.js 15 project
  ├── Configure TypeScript + ESLint
  ├── Setup Tailwind CSS with RTL
  └── Implement next-intl (EN/AR)

Phase 2: Foundational (BLOCKS all user stories)
  ├── Setup TanStack Query provider
  ├── Create Zod schemas (data-model.md)
  ├── Build API client (fetch wrapper)
  ├── Setup Vitest + Playwright
  └── Create base layout components

Phase 3: P1 - View Validation Results (MVP)
  ├── ResultCard component (medication line items)
  ├── StatusBadge component (✓/❌)
  ├── PatientHeader component
  └── Results page (/prescriptions/[jobId])

Phase 4: P2 - Upload Prescription
  ├── FileUploader component (react-dropzone)
  ├── File validation hook
  ├── Upload mutation (TanStack Query)
  └── Upload page (/)

Phase 5: P3 - Track Job Status
  ├── Polling hook (usePrescriptionPolling)
  ├── Status page with progress indicators
  └── Auto-redirect on completion

Phase 6: P4 - View Original Prescription
  └── PDFViewer component (@react-pdf-viewer)

Phase 7: P5 - Bilingual Support (cross-cutting)
  ├── Language switcher component
  ├── Translation files (messages/en.json, messages/ar.json)
  └── RTL layout testing
```

### Testing Strategy

**Unit Tests** (Vitest - 80% coverage):
- All hooks: `useFileUpload`, `usePrescriptionPolling`, `useRTL`
- Utility functions: `validate`, `formatters`, `cn`
- Pure components: `StatusBadge`, `PatientHeader`

**Component Tests** (Vitest + Testing Library - 60% coverage):
- `FileUploader` (drag-drop, validation)
- `ResultCard` (rendering line items)
- `MedicationCard` (bilingual display)
- `LanguageSwitcher` (locale toggle)

**Integration Tests** (Playwright + MSW):
- Upload flow with mocked backend
- Polling simulation (status transitions)
- Error boundary testing

**E2E Tests** (Playwright - 5 critical flows):
1. Complete upload → results flow
2. Invalid file upload (error handling)
3. Job status polling (EXTRACTING → COMPLETED)
4. Language toggle (EN → AR, RTL layout)
5. WCAG 2.1 AA accessibility (axe-core)

---

## Dependencies Installation

### Production Dependencies

```json
{
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.7.0",
    "next-intl": "^4.8.2",
    "@tanstack/react-query": "^5.90.20",
    "zustand": "^5.0.6",
    "zod": "^3.24.1",
    "react-hook-form": "^7.54.2",
    "@hookform/resolvers": "^3.9.1",
    "tailwindcss": "^3.4.0",
    "tailwindcss-rtl": "^0.9.0",
    "@react-pdf-viewer/core": "^1.17.0",
    "react-dropzone": "^14.3.5",
    "@radix-ui/react-alert-dialog": "^1.1.4",
    "@radix-ui/react-toast": "^1.2.4",
    "@radix-ui/react-select": "^2.2.1",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.7.0"
  }
}
```

### Development Dependencies

```json
{
  "devDependencies": {
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "@vitejs/plugin-react": "^4.3.4",
    "vitest": "^3.1.0",
    "@vitest/ui": "^3.1.0",
    "@playwright/test": "^1.50.0",
    "msw": "^2.7.0",
    "@axe-core/playwright": "^4.10.2",
    "eslint": "^9.18.0",
    "eslint-config-next": "^15.5.0",
    "prettier": "^3.4.2",
    "prettier-plugin-tailwindcss": "^0.7.3"
  }
}
```

---

## Environment Variables

### Development (`.env.local`)

```env
# Backend API base URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Enable React Query DevTools in production
NEXT_PUBLIC_ENABLE_DEVTOOLS=false

# Feature flags (future)
NEXT_PUBLIC_ENABLE_WEBSOCKETS=false
```

### Production (`.env.production`)

```env
NEXT_PUBLIC_API_URL=https://api.mediscan.example.com
NEXT_PUBLIC_ENABLE_DEVTOOLS=false
NEXT_PUBLIC_ENABLE_WEBSOCKETS=false
```

---

## Deployment Strategy

**Platform**: Vercel (recommended for Next.js App Router)

**Build Command**:
```bash
npm run build
```

**Output Directory**: `.next/`

**Environment Variables** (Vercel):
- `NEXT_PUBLIC_API_URL`: Production backend URL
- `NEXT_PUBLIC_ENABLE_DEVTOOLS`: `false`

**Post-Deployment Checklist**:
1. ✅ Verify CORS headers from backend allow production domain
2. ✅ Test file upload from production (10MB limit enforced)
3. ✅ Run Lighthouse audit (Performance >90, Accessibility 100)
4. ✅ Test bilingual support (EN/AR toggle, RTL layout)
5. ✅ Verify error boundaries display user-friendly messages
6. ✅ Test on mobile devices (iOS Safari, Android Chrome)
7. ✅ WCAG 2.1 AA audit (axe-core, manual keyboard navigation)

---

## Success Metrics

**Performance** (Lighthouse):
- Performance: >90
- Accessibility: 100 (WCAG 2.1 AA)
- Best Practices: >90
- SEO: >90

**User Experience**:
- Upload → Results: <60 seconds (including 20-50s backend processing)
- Language toggle: <1 second
- Results page render: <3 seconds
- Mobile responsiveness: 360px+ viewports

**Code Quality**:
- TypeScript strict mode: 0 type errors
- ESLint: 0 warnings/errors
- Test coverage: >80% unit, >60% component, 5 critical E2E flows

---

## Next Steps

**After this command**:
1. Run agent context update script (manual step)
2. Create tasks.md with `/speckit.tasks` command
3. Begin implementation following task order (setup → foundational → P1 MVP → P2 → P3 → P4 → P5)

**Command to proceed**:
```bash
/speckit.tasks
```

This will generate dependency-ordered task list from the design artifacts created in Phase 1.

---

## Artifacts Generated

This `/speckit.plan` command has generated:
- ✅ [plan.md](./plan.md) - This implementation plan
- ✅ [research.md](./research.md) - Technology research and decisions
- ✅ [data-model.md](./data-model.md) - TypeScript types and Zod schemas
- ✅ [quickstart.md](./quickstart.md) - Developer setup guide
- ✅ [contracts/frontend-api-contract.md](./contracts/frontend-api-contract.md) - API contract specification

**Planning Phase**: ✅ COMPLETE
**Ready for**: Task generation (`/speckit.tasks`) and implementation
