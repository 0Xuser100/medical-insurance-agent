# GCP Extraction Strategy for Prescriptions

## Does Document AI Have a Prescription Processor?

**No.** GCP Document AI does **NOT** have a dedicated prescription processor.

Available Document AI processors focus on:
- General OCR (Enterprise Document OCR)
- Financial documents (invoices, bank statements, W2)
- Identity documents (passports, driver's licenses)
- Custom extractors (requires training)

---

## Recommended Approach: Two-Step Pipeline

```
┌──────────────────┐      ┌─────────────────────────┐      ┌──────────────────┐
│  Prescription    │      │   Document AI           │      │  Healthcare NLP  │
│  Image/PDF       │─────▶│   (OCR → Raw Text)      │─────▶│  API (Entities)  │
└──────────────────┘      └─────────────────────────┘      └──────────────────┘
                                    │                               │
                               Raw text                    Structured output:
                               extraction                  - Medications
                                                          - Diagnoses (ICD)
                                                          - Procedures
                                                          - Dosages
```

---

## Step 1: Document AI (OCR)

Use **Enterprise Document OCR** or **Form Parser** to extract raw text from prescription images.

```python
from google.cloud import documentai_v1 as documentai

def extract_text_from_prescription(image_bytes: bytes, processor_name: str) -> str:
    """
    Extract raw text from prescription image using Document AI OCR.

    Args:
        image_bytes: The prescription image as bytes
        processor_name: Full resource name of your OCR processor

    Returns:
        Extracted text from the prescription
    """
    client = documentai.DocumentProcessorServiceClient()

    raw_document = documentai.RawDocument(
        content=image_bytes,
        mime_type="image/jpeg"  # or "application/pdf"
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    return result.document.text
```

### Setup Document AI Processor

1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai)
2. Create a new processor → Select **Document OCR**
3. Note the processor ID and location
4. Processor name format: `projects/{project}/locations/{location}/processors/{processor_id}`

---

## Step 2: Healthcare Natural Language API (Entity Extraction)

Pass the extracted text to **Healthcare NLP API** for medical entity recognition.

### What Healthcare NLP API Extracts

| Entity Type | Examples | Standard Code |
|-------------|----------|---------------|
| **Medications** | Azithromycin 500mg, Propranolol 40mg | RxNorm |
| **Diagnoses** | Acute Bronchitis, Hypertension | ICD-10 |
| **Procedures** | Chest X-Ray, CT Scan | CPT |
| **Body Parts** | Lungs, Heart | SNOMED |
| **Dosages** | 500mg, twice daily | - |

### Key Features

- **Auto-normalizes** to ICD-10, RxNorm, MeSH codes
- **Temporal awareness** - distinguishes past vs. current medications
- **Context awareness** - identifies patient vs. family history
- **HIPAA compliant**

### Code Example

```python
from google.cloud import healthcare_v1

def extract_medical_entities(text: str, nlp_service_name: str) -> dict:
    """
    Extract medical entities from text using Healthcare NLP API.

    Args:
        text: Raw text extracted from prescription
        nlp_service_name: Full resource name of NLP service

    Returns:
        Dictionary with medications, diagnoses, and procedures
    """
    client = healthcare_v1.HealthcareNaturalLanguageServiceClient()

    request = healthcare_v1.AnalyzeEntitiesRequest(
        nlp_service=nlp_service_name,
        document_content=text
    )

    response = client.analyze_entities(request=request)

    medications = []
    diagnoses = []
    procedures = []

    for entity in response.entities:
        entity_data = {
            "text": entity.text,
            "confidence": entity.confidence,
            "codes": []
        }

        # Extract vocabulary codes
        for vocab_code in entity.vocabulary_codes:
            entity_data["codes"].append({
                "system": vocab_code.vocabulary,
                "code": vocab_code.code
            })

        # Categorize by entity type
        if any("RXNORM" in str(c) for c in entity.vocabulary_codes):
            medications.append(entity_data)
        elif any("ICD" in str(c) for c in entity.vocabulary_codes):
            diagnoses.append(entity_data)
        elif any("CPT" in str(c) for c in entity.vocabulary_codes):
            procedures.append(entity_data)

    return {
        "medications": medications,
        "diagnoses": diagnoses,
        "procedures": procedures
    }
```

### Setup Healthcare NLP API

1. Enable the **Cloud Healthcare API** in your GCP project
2. Create a Healthcare dataset and NLP service
3. NLP service name format: `projects/{project}/locations/{location}/services/nlp`

---

## Complete Pipeline Example

```python
from google.cloud import documentai_v1 as documentai
from google.cloud import healthcare_v1
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExtractedPrescription:
    raw_text: str
    medications: list
    diagnoses: list
    procedures: list
    confidence: float

class PrescriptionExtractor:
    def __init__(
        self,
        project_id: str,
        location: str,
        docai_processor_id: str
    ):
        self.project_id = project_id
        self.location = location

        # Document AI setup
        self.docai_client = documentai.DocumentProcessorServiceClient()
        self.processor_name = (
            f"projects/{project_id}/locations/{location}"
            f"/processors/{docai_processor_id}"
        )

        # Healthcare NLP setup
        self.nlp_client = healthcare_v1.HealthcareNaturalLanguageServiceClient()
        self.nlp_service = f"projects/{project_id}/locations/{location}/services/nlp"

    def extract(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ExtractedPrescription:
        """
        Full extraction pipeline: Image → Text → Medical Entities
        """
        # Step 1: OCR
        raw_text = self._extract_text(image_bytes, mime_type)

        # Step 2: Entity extraction
        entities = self._extract_entities(raw_text)

        # Calculate overall confidence
        all_confidences = [
            e.get("confidence", 0)
            for category in entities.values()
            for e in category
        ]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

        return ExtractedPrescription(
            raw_text=raw_text,
            medications=entities["medications"],
            diagnoses=entities["diagnoses"],
            procedures=entities["procedures"],
            confidence=avg_confidence
        )

    def _extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Step 1: Document AI OCR"""
        raw_document = documentai.RawDocument(
            content=image_bytes,
            mime_type=mime_type
        )
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=raw_document
        )
        result = self.docai_client.process_document(request=request)
        return result.document.text

    def _extract_entities(self, text: str) -> dict:
        """Step 2: Healthcare NLP API"""
        request = healthcare_v1.AnalyzeEntitiesRequest(
            nlp_service=self.nlp_service,
            document_content=text
        )
        response = self.nlp_client.analyze_entities(request=request)

        medications = []
        diagnoses = []
        procedures = []

        for entity in response.entities:
            entity_data = {
                "text": entity.text,
                "confidence": entity.confidence,
                "codes": [
                    {"system": vc.vocabulary, "code": vc.code}
                    for vc in entity.vocabulary_codes
                ]
            }

            vocab_str = str(entity.vocabulary_codes)
            if "RXNORM" in vocab_str:
                medications.append(entity_data)
            elif "ICD" in vocab_str:
                diagnoses.append(entity_data)
            elif "CPT" in vocab_str:
                procedures.append(entity_data)

        return {
            "medications": medications,
            "diagnoses": diagnoses,
            "procedures": procedures
        }


# Usage
if __name__ == "__main__":
    extractor = PrescriptionExtractor(
        project_id="your-project-id",
        location="us-central1",
        docai_processor_id="your-ocr-processor-id"
    )

    with open("prescription.jpg", "rb") as f:
        image_bytes = f.read()

    result = extractor.extract(image_bytes)

    print(f"Raw Text: {result.raw_text[:200]}...")
    print(f"Medications: {result.medications}")
    print(f"Diagnoses: {result.diagnoses}")
    print(f"Confidence: {result.confidence:.2%}")
```

---

## Alternative: Custom Document AI Extractor

If Healthcare NLP API doesn't meet your needs, you can train a **Custom Extractor**:

### Steps

1. **Collect samples** - 50-100 labeled prescription images
2. **Define labels** - medication_name, dosage, frequency, diagnosis, etc.
3. **Upload & annotate** - Use Document AI Console
4. **Train** - Automatic training process
5. **Deploy** - Get processor endpoint

### Pros & Cons

| Aspect | Pros | Cons |
|--------|------|------|
| **Accuracy** | Tailored to your format | Requires labeled data |
| **Maintenance** | One-time setup | Needs retraining for new formats |
| **Cost** | Pay per use | Training costs |
| **Codes** | Can extract any field | No auto-normalization to ICD/RxNorm |

---

## API Comparison

| Feature | Document AI | Healthcare NLP API |
|---------|-------------|-------------------|
| **Input** | Images, PDFs | Text only |
| **Output** | Raw text, key-value pairs | Medical entities with codes |
| **Medical Codes** | No | Yes (ICD-10, RxNorm, MeSH) |
| **HIPAA** | Yes | Yes |
| **Custom Training** | Yes (Custom Extractor) | Yes (AutoML Entity Extraction) |
| **Best For** | OCR, form parsing | Medical text understanding |
| **Pricing** | Per page | Per 1000 characters |

---

## Pricing Estimates

### Document AI (OCR)

| Tier | Price |
|------|-------|
| First 1,000 pages/month | Free |
| 1,001 - 5M pages | $1.50 per 1,000 pages |
| 5M+ pages | $0.60 per 1,000 pages |

### Healthcare NLP API

| Tier | Price |
|------|-------|
| First 10,000 units/month | Free |
| Beyond free tier | $0.10 per 1,000 characters |

*Prices as of 2024. Check [GCP Pricing](https://cloud.google.com/pricing) for current rates.*

---

## Environment Setup

### Required APIs

Enable these APIs in your GCP project:

```bash
gcloud services enable documentai.googleapis.com
gcloud services enable healthcare.googleapis.com
```

### Dependencies

```txt
google-cloud-documentai>=2.0.0
google-cloud-healthcare>=1.0.0
```

### Authentication

```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Or use application default credentials
gcloud auth application-default login
```

---

## Sources

- [Document AI Processors List](https://docs.cloud.google.com/document-ai/docs/processors-list)
- [Healthcare Natural Language API](https://cloud.google.com/blog/topics/healthcare-life-sciences/now-in-preview-healthcare-natural-language-api-and-automl-entity-extraction-for-healthcare)
- [Medical Entity Extraction Guide](https://medium.com/google-cloud/medical-entity-extraction-on-google-cloud-a-comprehensive-guide-898d7a5fc173)
- [Cloud Healthcare API Documentation](https://cloud.google.com/healthcare-api)
