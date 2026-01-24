# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Medical Insurance Automated Approval System - an AI-powered engine that processes prescription images to generate approval, rejection, or warning reports with Human-in-the-Loop review for doctors.

## Architecture

The system follows a 5-stage pipeline:

1. **Ingestion** - Upload prescription image/PDF
2. **Extraction** - GCP Document AI (OCR) → Healthcare NLP API (entity extraction) *(to be added later)*
3. **Context Retrieval** - Query patient history (post-MVP)
4. **AI Validation Agent** - Runs three guardrails:
   - Clinical Match Check (medications/labs must match diagnosis)
   - Medication Limit Check (>5 medications = doctor review)
   - Medication Duration Check (minimum 2 weeks between same medication)
5. **Output** - Structured JSON for frontend consumption

## Agent Loop Structure

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   GOAL   │────▶│  THINK   │────▶│  TOOLS   │────▶│   LOOP   │
│ Validate │     │ Analyze  │     │ Execute  │     │ Until    │
│ Rx items │     │  items   │     │  checks  │     │  done    │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                        │
                                               ┌────────▼────────┐
                                               │  SUCCESS RATE   │
                                               │ confidence_score│
                                               └─────────────────┘
```

## Technology Stack

- **Package Manager**: uv (not pip)
- **Agent Framework**: CrewAI
- **API**: FastAPI (async)
- **LLM**: OpenAI (gpt-4o-mini)
- **OCR/Extraction**: GCP Document AI + Healthcare NLP API *(to be added)*
- **Clinical Validation**: Rules Engine + JSON Lookup
- **Schema Validation**: Pydantic
- **Architecture**: SOLID Principles

## SOLID Principles

| Principle | Application |
|-----------|-------------|
| **S** - Single Responsibility | Each validator handles ONE guardrail only |
| **O** - Open/Closed | Base `Validator` class - add new validators without modifying existing |
| **L** - Liskov Substitution | All validators implement `ValidatorProtocol` interface |
| **I** - Interface Segregation | Separate protocols: `ValidatorProtocol`, `ReportBuilderProtocol` |
| **D** - Dependency Inversion | Inject validators via constructor, not concrete classes |

## Project Structure

```
medical-insurance-agent/
├── pyproject.toml              # uv project config
├── .env.example                # Environment template
├── src/
│   ├── core/
│   │   └── protocols.py        # Abstract interfaces (SOLID - D, I)
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── validators/
│   │   ├── base.py             # BaseValidator (SOLID - O, L)
│   │   ├── clinical_match.py   # Guardrail 1 (SOLID - S)
│   │   ├── medication_limit.py # Guardrail 2 (SOLID - S)
│   │   └── medication_duration.py # Guardrail 3 (SOLID - S)
│   ├── services/
│   │   ├── validation_service.py  # Orchestrates validators (SOLID - D)
│   │   └── report_builder.py      # Builds JSON response (SOLID - S)
│   ├── agents/
│   │   └── validation_crew.py  # CrewAI agent + crew
│   ├── data/
│   │   └── diagnosis_mappings.json  # ICD-10 → valid medications/labs
│   └── api/
│       ├── main.py             # FastAPI async app
│       └── dependencies.py     # Dependency injection (SOLID - D)
└── tests/
    └── test_validators.py
```

## Key Commands

```bash
# Install dependencies
uv sync

# Run API server
uv run uvicorn src.api.main:app --reload

# Run tests
uv run pytest

# Run with different port
API_PORT=3000 uv run uvicorn src.api.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info |
| GET | `/health` | Health check |
| POST | `/validate` | Full validation with CrewAI agent |
| POST | `/validate/simple` | Rule-based validation only (faster) |
| GET | `/config` | Current configuration |

## Key Domain Concepts

- **Line-item validation**: Each medication/procedure validated independently (partial approvals possible)
- **Bilingual output**: `reason_en` / `reason_ar` for Arabic-speaking markets
- **Status values**: `APPROVED`, `FLAGGED`, `PENDING_REVIEW`
- **Risk levels**: `LOW`, `MEDIUM`, `HIGH`
- **Insurance tiers**: Gold, Silver, Bronze

## Environment Variables

```bash
OPENAI_API_KEY=sk-your-key        # Required for CrewAI
OPENAI_MODEL_NAME=gpt-4o-mini     # Optional (default: gpt-4o-mini)
MEDICATION_LIMIT=5                 # Optional (default: 5)
MIN_DURATION_DAYS=14               # Optional (default: 14)
API_HOST=0.0.0.0                   # Optional (default: 0.0.0.0)
API_PORT=8000                      # Optional (default: 8000)
```

## GCP Integration (Future)

Two-step extraction pipeline to be added:
1. Document AI OCR processor extracts raw text from images
2. Healthcare NLP API extracts medical entities (medications→RxNorm, diagnoses→ICD-10, procedures→CPT)

See `GCP_EXTRACTION.md` for detailed implementation examples and setup instructions.
