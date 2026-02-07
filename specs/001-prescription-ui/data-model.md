# Data Model: Next.js Prescription Validation UI

**Feature**: 001-prescription-ui
**Date**: 2026-02-07
**Source**: Backend API response schemas from Medical Insurance Validation API

---

## Overview

This document defines the TypeScript types and Zod schemas for the frontend application. All schemas mirror the backend FastAPI Pydantic models to ensure type-safe API communication.

---

## 1. Job Status Enum

### JobStatus

Represents the current state of a prescription processing job.

**Possible Values**:
- `UPLOADED` - File uploaded, awaiting processing
- `EXTRACTING` - OCR extraction in progress
- `VALIDATING` - AI validation in progress
- `COMPLETED` - Processing complete, results available
- `FAILED` - Processing failed with error

**Zod Schema**:
```typescript
export const JobStatusSchema = z.enum([
  'UPLOADED',
  'EXTRACTING',
  'VALIDATING',
  'COMPLETED',
  'FAILED'
]);

export type JobStatus = z.infer<typeof JobStatusSchema>;
```

---

## 2. Patient Profile

### Patient

Patient demographic information extracted from prescription.

**Fields**:
- `id`: string - Patient identifier from prescription or generated job_id
- `name`: string - Full patient name
- `age`: string - Patient age (may include units like "41" or "6.5 years")
- `gender`: string - Patient gender (Male/Female/Other)

**Zod Schema**:
```typescript
export const PatientSchema = z.object({
  id: z.string(),
  name: z.string(),
  age: z.string(),
  gender: z.string()
});

export type Patient = z.infer<typeof PatientSchema>;
```

**Validation Rules**:
- All fields are required (backend ensures "not found" fallback)
- Age is stored as string to preserve format (e.g., "6.5 years")
- Gender is free-text (not enum) to allow for cultural variations

---

## 3. Extracted Data

### ExtractedPatient

Patient information from OCR extraction (more detailed than Patient profile).

**Fields**:
- `name`: string
- `age`: string
- `gender`: string
- `id`: string

**Zod Schema**:
```typescript
export const ExtractedPatientSchema = z.object({
  name: z.string(),
  age: z.string(),
  gender: z.string(),
  id: z.string()
});
```

---

### Provider

Healthcare provider information extracted from prescription.

**Fields**:
- `name`: string - Provider full name
- `id`: string - Provider license/registration ID
- `facility`: string - Healthcare facility/clinic name

**Zod Schema**:
```typescript
export const ProviderSchema = z.object({
  name: z.string(),
  id: z.string(),
  facility: z.string()
});

export type Provider = z.infer<typeof ProviderSchema>;
```

---

### Diagnosis

Primary diagnosis information with ICD-10 coding.

**Fields**:
- `primary`: string - Primary diagnosis description
- `icd_code`: string - ICD-10 code for diagnosis

**Zod Schema**:
```typescript
export const DiagnosisSchema = z.object({
  primary: z.string(),
  icd_code: z.string()
});

export type Diagnosis = z.infer<typeof DiagnosisSchema>;
```

**Example**:
```json
{
  "primary": "Allergic Rhinitis",
  "icd_code": "J30.9"
}
```

---

### Medication

Medication item from prescription with dosage and frequency.

**Fields**:
- `name`: string - Medication name (may include brand/generic)
- `dosage`: string - Dosage amount (e.g., "20mg", "120mg")
- `frequency`: string - Administration frequency (e.g., "1x2" = twice daily)
- `duration`: string - Treatment duration
- `quantity`: string - Quantity prescribed

**Zod Schema**:
```typescript
export const MedicationSchema = z.object({
  name: z.string(),
  dosage: z.string(),
  frequency: z.string(),
  duration: z.string(),
  quantity: z.string()
});

export type Medication = z.infer<typeof MedicationSchema>;
```

**Field Notes**:
- All fields default to `"not found"` if missing from prescription
- Frontend should handle "not found" gracefully (display as "—" or hide field)

---

### LabAnalysis

Laboratory test requested in prescription.

**Fields**:
- `name`: string - Lab test name (e.g., "ESR", "CRP")
- `type`: string - Test type/category

**Zod Schema**:
```typescript
export const LabAnalysisSchema = z.object({
  name: z.string(),
  type: z.string()
});

export type LabAnalysis = z.infer<typeof LabAnalysisSchema>;
```

---

### ExtractedData

Complete OCR extraction result from prescription image/PDF.

**Fields**:
- `patient`: ExtractedPatient
- `provider`: Provider
- `diagnosis`: Diagnosis
- `medications`: Medication[]
- `labs`: LabAnalysis[]
- `date`: string - Prescription issue date

**Zod Schema**:
```typescript
export const ExtractedDataSchema = z.object({
  patient: ExtractedPatientSchema,
  provider: ProviderSchema,
  diagnosis: DiagnosisSchema,
  medications: z.array(MedicationSchema),
  labs: z.array(LabAnalysisSchema),
  date: z.string()
});

export type ExtractedData = z.infer<typeof ExtractedDataSchema>;
```

---

## 4. Validation Results

### ValidationDetails

Detailed validation information for a single medication or lab test.

**Fields**:
- `clinical_match`: boolean - Whether item is clinically appropriate for diagnosis
- `duration_check`: string | null - Refill interval validation result ("OK" or null)
- `reason_en`: string - English explanation of validation result
- `reason_ar`: string - Arabic explanation (مناسب سريرياً للتشخيص)

**Zod Schema**:
```typescript
export const ValidationDetailsSchema = z.object({
  clinical_match: z.boolean(),
  duration_check: z.string().nullable(),
  reason_en: z.string(),
  reason_ar: z.string()
});

export type ValidationDetails = z.infer<typeof ValidationDetailsSchema>;
```

**Example (Approved)**:
```json
{
  "clinical_match": true,
  "duration_check": "OK",
  "reason_en": "Clinically appropriate for diagnosis",
  "reason_ar": "مناسب سريرياً للتشخيص"
}
```

**Example (Rejected)**:
```json
{
  "clinical_match": false,
  "duration_check": null,
  "reason_en": "No diagnosis provided in prescription - cannot validate medication appropriateness",
  "reason_ar": "لا يوجد تشخيص في الوصفة الطبية - لا يمكن التحقق من ملاءمة الدواء"
}
```

---

### LineItem

Individual validation result for a medication or lab test.

**Fields**:
- `type`: "MEDICATION" | "LAB_ANALYSIS" - Item type
- `item_name`: string - Medication or lab test name
- `status`: "APPROVED" | "FLAGGED" - Validation outcome
- `ui_badge`: string - Display text for badge (✓ Approved, ❌ Rejected)
- `risk_level`: "LOW" | "MEDIUM" | "HIGH" - Risk assessment
- `validation_details`: ValidationDetails

**Zod Schema**:
```typescript
export const LineItemSchema = z.object({
  type: z.enum(['MEDICATION', 'LAB_ANALYSIS']),
  item_name: z.string(),
  status: z.enum(['APPROVED', 'FLAGGED']),
  ui_badge: z.string(),
  risk_level: z.enum(['LOW', 'MEDIUM', 'HIGH']),
  validation_details: ValidationDetailsSchema
});

export type LineItem = z.infer<typeof LineItemSchema>;
```

**UI Mapping**:
- `status: "APPROVED"` → Green badge, ✓ icon
- `status: "FLAGGED"` → Red badge, ❌ icon
- `risk_level: "HIGH"` → Bold text, warning icon

---

### AIValidationEngine

Overall validation result with confidence score and line items.

**Fields**:
- `overall_status`: "APPROVED" | "FLAGGED" - Overall prescription status
- `confidence_score`: string - AI confidence (0.0-1.0 as string)
- `medication_count`: string - Total medications validated
- `line_items`: LineItem[] - Individual validation results

**Zod Schema**:
```typescript
export const AIValidationEngineSchema = z.object({
  overall_status: z.enum(['APPROVED', 'FLAGGED']),
  confidence_score: z.string(),
  medication_count: z.string(),
  line_items: z.array(LineItemSchema)
});

export type AIValidationEngine = z.infer<typeof AIValidationEngineSchema>;
```

**Business Rules**:
- If any line_item has `status: "FLAGGED"`, overall_status is "FLAGGED"
- Confidence score "0.0" indicates validation failure (no diagnosis)
- Confidence score "1.0" indicates high confidence in approval

---

### ValidationResult

Complete validation result with metadata.

**Fields**:
- `transaction_id`: string - Unique transaction ID (REQ-YYYY-XXXX format)
- `timestamp`: string - ISO 8601 timestamp of validation completion
- `patient_profile`: Patient - Patient summary for display
- `ai_validation_engine`: AIValidationEngine - Validation results

**Zod Schema**:
```typescript
export const ValidationResultSchema = z.object({
  transaction_id: z.string(),
  timestamp: z.string(),
  patient_profile: PatientSchema,
  ai_validation_engine: AIValidationEngineSchema
});

export type ValidationResult = z.infer<typeof ValidationResultSchema>;
```

---

## 5. API Response Schemas

### UploadResponse

Response from `/upload` endpoint.

**Fields**:
- `job_id`: string - Unique job identifier (PAT-XXXXXXXXXXXX format)
- `status`: JobStatus - Initial status (always "UPLOADED")
- `created_at`: string - ISO 8601 timestamp
- `started_at`: string | null - Processing start time
- `completed_at`: string | null - Processing completion time
- `error`: string | null - Error message if upload failed

**Zod Schema**:
```typescript
export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  error: z.string().nullable()
});

export type UploadResponse = z.infer<typeof UploadResponseSchema>;
```

---

### JobResultResponse

Response from `/result/{job_id}` endpoint (complete job data).

**Fields**:
- `job_id`: string
- `status`: JobStatus
- `created_at`: string
- `started_at`: string | null
- `completed_at`: string | null
- `error`: string | null
- `extracted_data`: ExtractedData | null - Available after EXTRACTING phase
- `result`: ValidationResult | null - Available after COMPLETED status

**Zod Schema**:
```typescript
export const JobResultResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  error: z.string().nullable(),
  extracted_data: ExtractedDataSchema.nullable(),
  result: ValidationResultSchema.nullable()
});

export type JobResultResponse = z.infer<typeof JobResultResponseSchema>;
```

**State Transitions**:
```
UPLOADED → EXTRACTING → VALIDATING → COMPLETED
                    ↓           ↓
                  FAILED     FAILED
```

---

## 6. Client-Side Types

### LanguageCode

Supported interface languages.

**Zod Schema**:
```typescript
export const LanguageCodeSchema = z.enum(['en', 'ar']);
export type LanguageCode = z.infer<typeof LanguageCodeSchema>;
```

---

### UploadFile

Client-side file validation schema.

**Fields**:
- `file`: File - JavaScript File object
- `size`: number - File size in bytes (max 10MB)
- `type`: string - MIME type (image/*, application/pdf)

**Zod Schema**:
```typescript
export const UploadFileSchema = z.object({
  file: z.instanceof(File),
  size: z.number().max(10 * 1024 * 1024, 'File must be less than 10MB'),
  type: z.enum([
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/tiff',
    'application/pdf'
  ])
});

export type UploadFile = z.infer<typeof UploadFileSchema>;
```

---

## 7. Derived UI Types

### StatusBadgeProps

Props for status badge component.

**Fields**:
- `status`: "APPROVED" | "FLAGGED"
- `uiBadge`: string - Display text
- `riskLevel`: "LOW" | "MEDIUM" | "HIGH"

**TypeScript Interface**:
```typescript
export interface StatusBadgeProps {
  status: 'APPROVED' | 'FLAGGED';
  uiBadge: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}
```

---

### MedicationCardProps

Props for medication display card.

**Fields**:
- `lineItem`: LineItem
- `locale`: LanguageCode

**TypeScript Interface**:
```typescript
export interface MedicationCardProps {
  lineItem: LineItem;
  locale: LanguageCode;
}
```

---

## 8. Validation Helpers

### Runtime Validation Utility

```typescript
// lib/utils/validate.ts
import { ZodSchema } from 'zod';

export function validateApiResponse<T>(
  data: unknown,
  schema: ZodSchema<T>
): T {
  try {
    return schema.parse(data);
  } catch (error) {
    console.error('API response validation failed:', error);
    throw new Error('Invalid API response format');
  }
}

// Usage
const result = await fetch('/api/result/PAT-123').then(r => r.json());
const validated = validateApiResponse(result, JobResultResponseSchema);
```

---

## Entity Relationships

```
JobResultResponse
├── job_id (string)
├── status (JobStatus enum)
├── extracted_data (ExtractedData)
│   ├── patient (ExtractedPatient)
│   ├── provider (Provider)
│   ├── diagnosis (Diagnosis)
│   ├── medications[] (Medication)
│   └── labs[] (LabAnalysis)
└── result (ValidationResult)
    ├── transaction_id (string)
    ├── patient_profile (Patient)
    └── ai_validation_engine (AIValidationEngine)
        ├── overall_status (enum)
        ├── confidence_score (string)
        └── line_items[] (LineItem)
            ├── type (enum)
            ├── item_name (string)
            ├── status (enum)
            ├── ui_badge (string)
            ├── risk_level (enum)
            └── validation_details (ValidationDetails)
                ├── clinical_match (boolean)
                ├── duration_check (string | null)
                ├── reason_en (string)
                └── reason_ar (string)
```

---

## Notes

1. **String Numbers**: Backend returns numeric values as strings (`confidence_score`, `medication_count`) - keep as strings to preserve precision
2. **Nullable Fields**: Use `.nullable()` in Zod for optional API fields
3. **Default Values**: Backend uses `"not found"` as placeholder - frontend should display as "—" or hide field
4. **Bilingual Content**: Always display both `reason_en` and `reason_ar` based on user language preference
5. **Type Safety**: Use `z.infer<typeof Schema>` to generate TypeScript types from Zod schemas
