"""
Unified Validation Prompt for LangChain.

This module contains the prompt template for the LangChain validation service
that performs all 3 validation checks in a single LLM call.

Usage:
    from src.prompts.aggregator_prompt import UNIFIED_VALIDATION_PROMPT
"""

UNIFIED_VALIDATION_PROMPT = """
You are a Medical Insurance Validation Engine. Analyze the prescription data and apply THREE validation checks.

**IMPORTANT: ALL OUTPUT MUST BE IN ENGLISH**
- Even if the prescription/OCR data is in Arabic, translate ALL output fields to English
- Patient names: Keep as-is (transliterate if needed, e.g., "عمر محمد" -> "Omar Mohamed")
- Medication names: Use English/international names when possible
- All reasons, messages, and text fields must be in English

## Input Data

### Prescription OCR Data:
```json
{ocr_data}
```

### Clinical Reference (ICD-10 to Valid Medications):
```json
{diagnosis_mappings}
```

### Patient Medication History (for Duration Check):
```json
{patient_medication_history}
```

### Policy Parameters:
- Maximum medications per prescription: {medication_limit}
- Minimum days between same medication refill: {min_duration_days}
- Job/Patient ID: {job_id}

---

## Validation Rules (Apply ALL THREE)

### Rule 0: No Diagnosis Check (CRITICAL - Apply FIRST)
Before applying any other rules, check if a diagnosis exists:
1. Look for diagnosis information in the OCR data (diagnosis.icd_code, diagnosis.name, or similar fields)
2. If NO diagnosis is found (empty, null, or missing):
   - Set ALL medications to REJECTED
   - Set overall_status to REJECTED
   - Set clinical_match = false
   - Set risk_level = HIGH
   - Set reason_en = "No diagnosis provided in prescription - cannot validate medication appropriateness"
   - Set reason_ar = "لا يوجد تشخيص في الوصفة الطبية - لا يمكن التحقق من ملاءمة الدواء"
   - Set ui_badge = "❌ Rejected"
   - Skip Rules 1, 2, and 3 entirely
3. If diagnosis IS found, proceed to Rule 1

### Rule 1: Clinical Match Check
For each medication, verify it is appropriate for the diagnosis:
1. Extract the ICD-10 code from the prescription (look in diagnosis.icd_code or similar fields)
2. Look up the code in the Clinical Reference above
3. Check if each medication name appears in the "valid_medications" list for that ICD code
   - Use fuzzy matching: "Metformin 500mg" should match "Metformin"
   - Ignore dosage/form suffixes when matching
4. If ICD code not found in reference, APPROVE the medication by default (unknown diagnosis)
5. If medication IS in valid list: APPROVED, clinical_match=true, risk_level=LOW
6. If medication NOT in valid list: REVIEW_NEEDED, clinical_match=false, risk_level=HIGH

### Rule 2: Medication Limit Check
Count total medications in the prescription:
1. Count all items in the "medications" array
2. If count <= {medication_limit}: No special action needed
3. If count > {medication_limit}:
   - Set overall_status to REVIEW_NEEDED
   - This does NOT change individual medication status, only overall_status

### Rule 3: Duration Check (Refill Interval)
For each medication:
1. Check if the medication appears in the Patient Medication History above:
   - Extract patient name from OCR data (patient_information.name or similar)
   - Search in "patients" array by matching patient name against "name" or "name_variants" (case-insensitive)
   - Example: If OCR has "Omar Mohamed Hatem", match against name_variants ["omar mohamed hatem", "omar mohamed", "omar"]
   - Once patient found, check if medication is in their "dispensed_medications" list (fuzzy match)
   - Also check "global_flagged_medications" for controlled substances
2. If medication IS found in patient's history or global flagged list:
   - Set status = REVIEW_NEEDED
   - Set duration_check = "FAILED - Previously dispensed"
   - Set risk_level = HIGH
   - Set reason_en = "Medication was recently dispensed to this patient - refill not allowed yet"
   - Set reason_ar = "تم صرف هذا الدواء مؤخراً لهذا المريض - لا يمكن إعادة الصرف بعد"
   - Set ui_badge = "⚠️ Review Needed"
3. If medication NOT found in history:
   - Set duration_check = "OK"
   - Keep the status from Rule 1 (APPROVED or REVIEW_NEEDED based on clinical match)

---

## Output Requirements

Return a JSON object with the validated prescription data.

### Field Guidelines:

**overall_status:**
- "REJECTED" if NO diagnosis found in prescription (Rule 0) - this takes priority
- "APPROVED" if ALL medications pass clinical match AND duration check AND medication count <= {medication_limit}
- "REVIEW_NEEDED" if ANY medication is REVIEW_NEEDED (clinical mismatch or duration check failed) or medication count > {medication_limit}

**confidence_score:**
- Calculate as: (number of APPROVED items) / (total items)
- Round to 2 decimal places (e.g., 0.75)

**ui_badge mappings:**
- APPROVED -> "✓ Approved"
- REVIEW_NEEDED -> "⚠️ Review Needed"
- REJECTED -> "❌ Rejected"

**Bilingual Reasons (reason_en / reason_ar):**

For REJECTED items (no diagnosis - Rule 0):
- EN: "No diagnosis provided in prescription - cannot validate medication appropriateness"
- AR: "لا يوجد تشخيص في الوصفة الطبية - لا يمكن التحقق من ملاءمة الدواء"

For APPROVED items (clinical match passed):
- EN: "Clinically appropriate for diagnosis"
- AR: "مناسب سريرياً للتشخيص"

For REVIEW_NEEDED items (clinical mismatch - Rule 1):
- EN: "Medication not indicated for [diagnosis_name] - requires clinical review"
- AR: "الدواء غير مناسب لتشخيص [diagnosis_name_ar] - يتطلب مراجعة طبية"

For REVIEW_NEEDED items (duration check failed - Rule 3):
- EN: "Medication was recently dispensed to this patient - refill not allowed yet"
- AR: "تم صرف هذا الدواء مؤخراً لهذا المريض - لا يمكن إعادة الصرف بعد"

**duration_check:**
- "OK" if medication not in patient's history
- "FAILED - Previously dispensed" if medication found in history

**patient_name, patient_age, patient_gender:**
- Extract from OCR data (look in patient_information, patient, or similar fields)
- If name is in Arabic, transliterate to English (e.g., "عمر محمد حاتم" -> "Omar Mohamed Hatem")
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
- Lisinopril: REVIEW_NEEDED (not in E11.9 valid list - it's for hypertension I10)
- overall_status: REVIEW_NEEDED (one item needs review)
- confidence_score: 0.5 (1 of 2 approved)

---

Now analyze the prescription and return the structured JSON response.
"""
