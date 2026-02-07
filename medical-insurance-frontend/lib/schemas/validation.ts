import { z } from "zod/v4";

export const JobStatusSchema = z.enum([
  "UPLOADED",
  "EXTRACTING",
  "VALIDATING",
  "COMPLETED",
  "FAILED",
]);
export type JobStatus = z.infer<typeof JobStatusSchema>;

export const ExtractedPatientSchema = z.object({
  name: z.string(),
  age: z.string(),
  gender: z.string(),
  id: z.string(),
});

export const ProviderSchema = z.object({
  name: z.string(),
  id: z.string(),
  facility: z.string(),
});
export type Provider = z.infer<typeof ProviderSchema>;

export const DiagnosisSchema = z.object({
  primary: z.string(),
  icd_code: z.string(),
});
export type Diagnosis = z.infer<typeof DiagnosisSchema>;

export const MedicationSchema = z.object({
  name: z.string(),
  dosage: z.string(),
  frequency: z.string(),
  duration: z.string(),
  quantity: z.string(),
});
export type Medication = z.infer<typeof MedicationSchema>;

export const LabAnalysisSchema = z.object({
  name: z.string(),
  type: z.string(),
});
export type LabAnalysis = z.infer<typeof LabAnalysisSchema>;

export const ExtractedDataSchema = z.object({
  patient: ExtractedPatientSchema,
  provider: ProviderSchema,
  diagnosis: DiagnosisSchema,
  medications: z.array(MedicationSchema),
  labs: z.array(LabAnalysisSchema),
  date: z.string(),
});
export type ExtractedData = z.infer<typeof ExtractedDataSchema>;

export const ValidationDetailsSchema = z.object({
  clinical_match: z.boolean(),
  duration_check: z.string().nullable(),
  reason_en: z.string(),
  reason_ar: z.string(),
});
export type ValidationDetails = z.infer<typeof ValidationDetailsSchema>;

export const LineItemSchema = z.object({
  type: z.enum(["MEDICATION", "LAB_ANALYSIS"]),
  item_name: z.string(),
  status: z.enum(["APPROVED", "REJECTED"]),
  ui_badge: z.string(),
  risk_level: z.enum(["LOW", "MEDIUM", "HIGH"]),
  validation_details: ValidationDetailsSchema,
});
export type LineItem = z.infer<typeof LineItemSchema>;

export const PatientProfileSchema = z.object({
  id: z.string(),
  name: z.string(),
  age: z.string(),
  gender: z.string(),
});
export type PatientProfile = z.infer<typeof PatientProfileSchema>;

export const AIValidationEngineSchema = z.object({
  overall_status: z.enum(["APPROVED", "REJECTED"]),
  confidence_score: z.string(),
  medication_count: z.string(),
  line_items: z.array(LineItemSchema),
});
export type AIValidationEngine = z.infer<typeof AIValidationEngineSchema>;

export const ValidationResultSchema = z.object({
  transaction_id: z.string(),
  timestamp: z.string(),
  patient_profile: PatientProfileSchema,
  ai_validation_engine: AIValidationEngineSchema,
});
export type ValidationResult = z.infer<typeof ValidationResultSchema>;

export const JobResultResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  error: z.string().nullable(),
  extracted_data: ExtractedDataSchema.nullable().optional(),
  result: ValidationResultSchema.nullable().optional(),
});
export type JobResultResponse = z.infer<typeof JobResultResponseSchema>;

export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  filename: z.string(),
  file_size: z.number(),
  created_at: z.string(),
  message: z.string(),
});
export type UploadResponse = z.infer<typeof UploadResponseSchema>;
