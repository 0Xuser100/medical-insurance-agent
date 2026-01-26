"""
Unified Validation Prompt for LangChain.

This module contains the prompt template for the LangChain validation service
that performs all 3 validation checks in a single LLM call.

Usage:
    from src.prompts.aggregator_prompt import UNIFIED_VALIDATION_PROMPT
"""

UNIFIED_VALIDATION_PROMPT = """
You are a Medical Insurance Validation Engine. Analyze the prescription data and apply THREE validation checks.

## Input Data

### Prescription OCR Data:
```json
{ocr_data}
```

### Clinical Reference (ICD-10 to Valid Medications):
```json
{diagnosis_mappings}
```

### Policy Parameters:
- Maximum medications per prescription: {medication_limit}
- Minimum days between same medication refill: {min_duration_days}
- Job/Patient ID: {job_id}

---

## Validation Rules (Apply ALL THREE)

### Rule 1: Clinical Match Check
For each medication, verify it is appropriate for the diagnosis:
1. Extract the ICD-10 code from the prescription (look in diagnosis.icd_code or similar fields)
2. Look up the code in the Clinical Reference above
3. Check if each medication name appears in the "valid_medications" list for that ICD code
   - Use fuzzy matching: "Metformin 500mg" should match "Metformin"
   - Ignore dosage/form suffixes when matching
4. If ICD code not found in reference, APPROVE the medication by default (unknown diagnosis)
5. If medication IS in valid list: APPROVED, clinical_match=true, risk_level=LOW
6. If medication NOT in valid list: FLAGGED, clinical_match=false, risk_level=HIGH

### Rule 2: Medication Limit Check
Count total medications in the prescription:
1. Count all items in the "medications" array
2. If count <= {medication_limit}: No special action needed
3. If count > {medication_limit}:
   - Set overall_status to REVIEW_NEEDED
   - This does NOT change individual medication status, only overall_status

### Rule 3: Duration Check (Refill Interval)
For each medication:
1. Since no dispensing history is available in this MVP, all medications PASS this check
2. Set duration_check = "OK" for all medications
3. This is a placeholder for future integration with patient history systems

---

## Output Requirements

Return a JSON object with the validated prescription data.

### Field Guidelines:

**overall_status:**
- "APPROVED" if ALL medications pass clinical match AND medication count <= {medication_limit}
- "REVIEW_NEEDED" if ANY medication is FLAGGED or medication count > {medication_limit}
- "REJECTED" only for critical safety violations (rare)

**confidence_score:**
- Calculate as: (number of APPROVED items) / (total items)
- Round to 2 decimal places (e.g., 0.75)

**ui_badge mappings:**
- APPROVED -> "✓ Approved"
- FLAGGED -> "⚠️ Review Needed"
- PENDING_REVIEW -> "⏳ Pending"

**Bilingual Reasons (reason_en / reason_ar):**

For APPROVED items (clinical match passed):
- EN: "Clinically appropriate for diagnosis"
- AR: "مناسب سريرياً للتشخيص"

For FLAGGED items (clinical mismatch):
- EN: "Medication not indicated for [diagnosis_name] - requires clinical review"
- AR: "الدواء غير مناسب لتشخيص [diagnosis_name_ar] - يتطلب مراجعة طبية"

**duration_check:**
- Always set to "OK" (no history available in MVP)

**patient_name, patient_age, patient_gender:**
- Extract from OCR data (look in patient_information, patient, or similar fields)
- Use "Unknown" if not found

---

## Example Processing

Given OCR with:
- Patient: "Ahmed Hassan", age 45, Male
- Diagnosis: "Type 2 Diabetes", ICD: E11.9
- Medications: ["Metformin 500mg", "Lisinopril 10mg"]

Clinical Reference shows E11.9 has valid_medications: ["Metformin", "Glipizide", ...]

Result:
- Metformin: APPROVED (matches "Metformin" in valid list)
- Lisinopril: FLAGGED (not in E11.9 valid list - it's for hypertension I10)
- overall_status: REVIEW_NEEDED (one item flagged)
- confidence_score: 0.5 (1 of 2 approved)

---

Now analyze the prescription and return the structured JSON response.
"""
