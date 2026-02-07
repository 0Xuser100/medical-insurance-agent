# Feature Specification: Next.js Prescription Validation UI

**Feature Branch**: `001-prescription-ui`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "Next.js UI for prescription validation system"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Validation Results (Priority: P1)

Healthcare administrators need to review AI-generated prescription validation results with clear visual indicators for approved and rejected medications, including bilingual explanations.

**Why this priority**: This is the core value proposition - displaying validation results is the primary reason users interact with the system. Without this, the UI serves no purpose.

**Independent Test**: Can be fully tested by providing a mock validation result JSON and verifying all sections render correctly with proper status badges, bilingual text, and patient information.

**Acceptance Scenarios**:

1. **Given** a completed validation result, **When** user navigates to the results page, **Then** patient information (name, age, gender, ID) is displayed prominently at the top
2. **Given** a validation result with multiple medications, **When** results are displayed, **Then** each medication shows a status badge (✓ Approved or ❌ Rejected) with color coding (green for approved, red for rejected)
3. **Given** a rejected medication, **When** user views the medication card, **Then** both English and Arabic rejection reasons are displayed clearly
4. **Given** a validation result with labs/analyses, **When** results are displayed, **Then** requested labs are shown with their validation status
5. **Given** a validation result, **When** user views the page, **Then** overall validation status (APPROVED/REJECTED) is prominently displayed with confidence score
6. **Given** a completed validation, **When** results are displayed, **Then** transaction ID and timestamp are visible for audit trail purposes

---

### User Story 2 - Upload Prescription for Analysis (Priority: P2)

Healthcare administrators need to upload prescription images or PDFs to initiate the AI validation process.

**Why this priority**: This is the entry point to the workflow. While viewing results is more critical, users need a way to submit prescriptions. This can be built independently as a separate page.

**Independent Test**: Can be fully tested by uploading a valid prescription file, receiving a job_id, and verifying the upload confirmation without needing the full validation pipeline.

**Acceptance Scenarios**:

1. **Given** user is on the upload page, **When** user selects a prescription file (JPEG, PNG, PDF), **Then** file is validated for type and size (max 10MB)
2. **Given** a valid prescription file, **When** user clicks upload, **Then** file is uploaded and a job_id is returned with status "UPLOADED"
3. **Given** an invalid file type, **When** user attempts upload, **Then** clear error message is displayed in both English and Arabic
4. **Given** file size exceeds 10MB, **When** user attempts upload, **Then** error message indicates file is too large
5. **Given** successful upload, **When** processing begins, **Then** user is redirected to a status tracking page with the job_id
6. **Given** upload in progress, **When** waiting for completion, **Then** user sees a loading indicator with estimated time

---

### User Story 3 - Track Job Status (Priority: P3)

Healthcare administrators need to monitor the progress of prescription validation jobs through different stages (UPLOADED, EXTRACTING, VALIDATING, COMPLETED, FAILED).

**Why this priority**: For async processing, users need feedback on progress. This enhances UX but the core value is viewing results. Can be implemented independently as a status polling page.

**Independent Test**: Can be fully tested by polling a mock job endpoint that returns different status values, verifying UI updates correctly for each status.

**Acceptance Scenarios**:

1. **Given** a job is in EXTRACTING status, **When** status page loads, **Then** user sees "Extracting prescription data..." with progress indicator
2. **Given** a job is in VALIDATING status, **When** status page loads, **Then** user sees "Validating medications..." with progress indicator
3. **Given** a job transitions to COMPLETED, **When** status page auto-refreshes, **Then** user is automatically redirected to results page
4. **Given** a job transitions to FAILED, **When** status page auto-refreshes, **Then** error message is displayed with option to retry
5. **Given** user closes browser during processing, **When** user returns with job_id, **Then** status can be resumed from URL

---

### User Story 4 - View Original Prescription (Priority: P4)

Healthcare administrators need to view the original prescription image/PDF alongside validation results for verification and dispute resolution.

**Why this priority**: Important for audit and verification but not core to the validation workflow. Can be added as an overlay/modal feature independently.

**Independent Test**: Can be fully tested by clicking "View Original Prescription" button and verifying the image/PDF modal displays correctly.

**Acceptance Scenarios**:

1. **Given** validation results are displayed, **When** user clicks "View Original Prescription" button, **Then** original prescription image opens in a modal or new tab
2. **Given** prescription is a PDF, **When** user views original, **Then** PDF renders with zoom and page navigation controls
3. **Given** prescription is an image, **When** user views original, **Then** image displays at full resolution with zoom capability
4. **Given** original prescription is displayed, **When** user closes modal, **Then** user returns to validation results page

---

### User Story 5 - Bilingual Interface Support (Priority: P5)

Healthcare administrators working in bilingual regions need the entire interface to support both English and Arabic with proper RTL (right-to-left) rendering for Arabic.

**Why this priority**: Critical for accessibility in bilingual healthcare environments but can be implemented as a language toggle feature independently without blocking other stories.

**Independent Test**: Can be fully tested by toggling language and verifying all UI elements, labels, and content switch languages correctly with proper text direction.

**Acceptance Scenarios**:

1. **Given** user is on any page, **When** user clicks language toggle, **Then** entire interface switches between English and Arabic
2. **Given** Arabic language is selected, **When** page renders, **Then** layout switches to RTL (right-to-left) with proper alignment
3. **Given** validation results contain bilingual reasons, **When** English is selected, **Then** only English reasons are displayed
4. **Given** validation results contain bilingual reasons, **When** Arabic is selected, **Then** only Arabic reasons are displayed
5. **Given** user preference is saved, **When** user returns to the site, **Then** last selected language is remembered

---

### Edge Cases

- What happens when API returns incomplete data (missing patient name, age, or diagnosis)?
- How does the UI handle extremely long medication names or rejection reasons?
- What happens when confidence_score is null or zero?
- How does the system handle network timeouts during job status polling?
- What happens when job_id in URL is invalid or expired?
- How does UI handle a prescription with 20+ medications (scrolling, pagination)?
- What happens when both reason_en and reason_ar are missing in validation results?
- How does UI respond when original prescription file is no longer available?
- What happens when user uploads a file while another job is still processing?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display patient information (name, age, gender, ID) from validation results
- **FR-002**: System MUST render medication validation cards with status badges (✓ Approved, ❌ Rejected) using color coding
- **FR-003**: System MUST display bilingual rejection/approval reasons for each medication (reason_en and reason_ar)
- **FR-004**: System MUST show overall validation status (APPROVED/REJECTED) with confidence score
- **FR-005**: System MUST display extracted diagnosis information with ICD code when available
- **FR-006**: System MUST render requested lab analyses with their validation status
- **FR-007**: System MUST provide file upload functionality supporting JPEG, PNG, GIF, WebP, TIFF, and PDF formats with 10MB size limit
- **FR-008**: System MUST validate file type and size before upload and display error messages bilingually
- **FR-009**: System MUST poll job status at regular intervals and update UI without page refresh
- **FR-010**: System MUST display transaction ID and timestamp for audit purposes
- **FR-011**: System MUST provide "View Original Prescription" button that displays the uploaded file
- **FR-012**: System MUST support language toggle between English and Arabic with RTL layout for Arabic
- **FR-013**: System MUST display appropriate loading states during upload, extraction, and validation phases
- **FR-014**: System MUST handle API errors gracefully with user-friendly bilingual error messages
- **FR-015**: System MUST allow direct navigation to job results via URL with job_id parameter
- **FR-016**: System MUST display AI confidence score and medication count in validation summary
- **FR-017**: System MUST show risk level indicators (HIGH, MEDIUM, LOW) for each validated item
- **FR-018**: System MUST provide action buttons ("Confirm & Sign", "View Original") based on validation completion
- **FR-019**: System MUST display provider information (name, facility) when available in extracted data
- **FR-020**: System MUST render prescription date and refill information when available

### Key Entities

- **ValidationResult**: Complete API response containing job_id, status, extracted_data, result, timestamps, and error information
- **Patient**: Patient profile data including id, name, age, gender extracted from prescription
- **Medication**: Individual medication item with name, dosage, frequency, duration, and validation status
- **ValidationDetails**: Per-item validation including clinical_match, duration_check, risk_level, and bilingual reasons
- **DiagnosisInfo**: Extracted diagnosis with primary condition and ICD code
- **LabAnalysis**: Requested laboratory tests with name, type, and validation status
- **JobStatus**: Current state of processing (UPLOADED, EXTRACTING, VALIDATING, COMPLETED, FAILED)
- **Provider**: Healthcare provider information including name, facility, and ID
- **UIBadge**: Visual indicator for item status (✓ Approved, ❌ Rejected, ⏳ Pending)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Healthcare administrators can view complete validation results in under 3 seconds after job completion
- **SC-002**: Users can upload a prescription file and receive upload confirmation in under 5 seconds
- **SC-003**: 95% of validation result pages render all sections correctly without missing data errors
- **SC-004**: Language toggle switches entire interface between English and Arabic in under 1 second
- **SC-005**: Job status updates automatically within 2 seconds of backend status change
- **SC-006**: Original prescription images load and display in under 3 seconds
- **SC-007**: 90% of users can interpret medication approval/rejection status without reading detailed reasons (based on visual indicators alone)
- **SC-008**: UI remains responsive and usable with prescriptions containing up to 50 medications
- **SC-009**: All critical user actions (upload, view results, language toggle) work on mobile devices (viewport width 360px+)
- **SC-010**: Error states display actionable recovery steps 100% of the time
- **SC-011**: Users can successfully navigate directly to job results via shared URL with job_id
- **SC-012**: RTL layout for Arabic text renders correctly with proper alignment in all sections

## Assumptions

- API endpoints follow the structure documented in the Medical Insurance Validation API (see README.md)
- Backend API is already deployed and accessible at a configurable base URL
- Authentication/authorization is handled separately (not part of this UI scope)
- File upload size limit of 10MB is enforced by both frontend validation and backend
- Job status polling interval will be 2 seconds during active processing
- Supported browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Mobile-first responsive design targeting viewports from 360px width upward
- User session management and job_id persistence handled via URL parameters or local storage
- Original prescription files remain accessible via API for the lifetime of the job record
- Default language is English; Arabic is available via toggle
- Color coding follows accessibility standards (WCAG 2.1 AA for contrast ratios)
