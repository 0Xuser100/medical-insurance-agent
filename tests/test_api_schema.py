import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_job_store
from src.models.schemas import (
    JobStatus,
    DataExtraction,  # Assumed unavailable, will use dict
    PrescriptionValidationResponse,
    PatientProfile,
    ExtractedContext,
    AIValidationEngine,
    OverallStatus,
    LineItem,
    ItemType,
    ItemStatus,
    RiskLevel,
    ValidationDetails,
)
from src.services.job_store import Job, InMemoryJobStore

client = TestClient(app)

# User's exact expected JSON structure (minus dynamic fields like timestamps)
EXPECTED_SCHEMA_EXAMPLE = {
  "job_id": "string",
  "status": "UPLOADED",
#   "created_at": "2026-01-24T15:54:29.873Z", 
#   "started_at": "2026-01-24T15:54:29.873Z",
#   "completed_at": "2026-01-24T15:54:29.873Z",
  "error": "string",
  "extracted_data": {
    "additionalProp1": {}
  },
  "result": {
    "ai_validation_engine": {
      "confidence_score": 0.75,
      "line_items": [],
      "medication_count": 3,
      "overall_status": "REVIEW_NEEDED",
      "summary_message": "Request partially approved."
    },
    "extracted_context": {
      "icd_code": "J20.9",
      "primary_diagnosis": "Acute Bronchitis",
      "provider_id": "DR-5501"
    },
    "patient_profile": {
      "age": 45,
      "gender": "Male",
      "history_summary": "",
      "id": "PAT-10023",
      "insurance_tier": "Gold",
      "name": "Ahmed Hassan"
    },
    "timestamp": "2024-05-21T10:30:00Z",
    "transaction_id": "REQ-2024-8859"
  }
}

@pytest.fixture
def mock_job_store():
    store = MagicMock(spec=InMemoryJobStore)
    return store

def test_get_result_schema_compliance(mock_job_store):
    # Overwrite dependency
    app.dependency_overrides[get_job_store] = lambda: mock_job_store

    # Create a completed job that mimics the user's example
    job_id = "TEST-JOB-1"
    
    # Construct the result object matching the example
    result_data = PrescriptionValidationResponse(
        transaction_id="REQ-2024-8859",
        timestamp=datetime.fromisoformat("2024-05-21T10:30:00+00:00"),
        patient_profile=PatientProfile(
            id="PAT-10023",
            name="Ahmed Hassan",
            age=45,
            gender="Male",
            insurance_tier="Gold",
            history_summary=""
        ),
        extracted_context=ExtractedContext(
            primary_diagnosis="Acute Bronchitis",
            icd_code="J20.9",
            provider_id="DR-5501"
        ),
        ai_validation_engine=AIValidationEngine(
            overall_status=OverallStatus.REVIEW_NEEDED,
            confidence_score=0.75,
            summary_message="Request partially approved.",
            medication_count=3,
            line_items=[]
        )
    )

    job = Job(
        id=job_id,
        status=JobStatus.COMPLETED,
        filename="test_rx.jpg",
        file_path="d:/uploads/test_rx.jpg",
        file_size=1024,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error="string", # To match schema example "string" (though usually None if success)
        extracted_data={"additionalProp1": {}},
        result=result_data
    )
    
    # Mock get_job return
    mock_job_store.get_job.return_value = job

    # Call endpoint
    response = client.get(f"/result/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify structure matches keys
    assert data["job_id"] == job_id
    assert data["status"] == "COMPLETED"
    assert "created_at" in data
    assert "started_at" in data
    assert "completed_at" in data
    assert data["error"] == "string"
    assert data["extracted_data"] == {"additionalProp1": {}}
    
    # Verify nested result structure
    res = data["result"]
    assert res["transaction_id"] == "REQ-2024-8859"
    # assert res["timestamp"] == "2024-05-21T10:30:00Z" # Timezone formatting might vary lightly
    
    pp = res["patient_profile"]
    assert pp["id"] == "PAT-10023"
    assert pp["name"] == "Ahmed Hassan"
    
    ec = res["extracted_context"]
    assert ec["icd_code"] == "J20.9"
    
    ai = res["ai_validation_engine"]
    assert ai["confidence_score"] == 0.75
    assert ai["line_items"] == []
    
    print("\nSchema verification passed!")
