# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Medical Insurance Automated Approval System - an AI-powered engine that processes prescription images to generate approval, rejection, or warning reports with Human-in-the-Loop review for doctors.

## Architecture

The system follows a 5-stage pipeline:

1. **Ingestion** - Upload prescription image/PDF
2. **Extraction** - Gemini OCR extracts data from images/PDFs
3. **AI Validation Agent** - CrewAI multi-agent system runs three guardrails:
   - Clinical Match Check (medications/labs must match diagnosis)
   - Medication Limit Check (>5 medications = doctor review)
   - Medication Duration Check (minimum 2 weeks between same medication)
4. **LLM Aggregation** - Gemini synthesizes OCR data + agent results into structured response
5. **Output** - Structured JSON with bilingual reasons (EN/AR) for frontend consumption

See `LLM_AGGREGATOR_README.md` for detailed information about the aggregation layer.

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
- **LLM (Agents)**: OpenAI (gpt-4o-mini)
- **LLM (OCR/Aggregation)**: Gemini (gemini-3-flash-preview)
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
├── LLM_AGGREGATOR_README.md    # LLM aggregator documentation
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
│   │   ├── validation_service.py     # Orchestrates validators (SOLID - D)
│   │   ├── report_builder.py         # Builds JSON response (SOLID - S)
│   │   └── llm_aggregator_service.py # LLM-based response synthesis
│   ├── agents/
│   │   └── validation_crew.py  # CrewAI agent + crew
│   ├── prompts/
│   │   ├── __init__.py             # Package exports
│   │   └── aggregator_prompt.py    # LLM aggregation prompt template
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
| GET | `/health` | Health check / API info |
| POST | `/upload` | Upload prescription image/PDF |
| POST | `/process` | Start async processing (extraction + validation + aggregation) |
| GET | `/result/{job_id}` | Poll for processing result |
| DELETE | `/job/{job_id}` | Cancel/delete a job |
| GET | `/jobs` | List all jobs (with optional status filter) |

## Key Domain Concepts

- **Line-item validation**: Each medication/procedure validated independently (partial approvals possible)
- **Bilingual output**: `reason_en` / `reason_ar` for Arabic-speaking markets
- **Status values**: `APPROVED`, `FLAGGED`, `PENDING_REVIEW`
- **Risk levels**: `LOW`, `MEDIUM`, `HIGH`
- **Insurance tiers**: Gold, Silver, Bronze

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key        # Required for CrewAI agents
GEMINI_API_KEY=your-gemini-key    # Required for OCR + LLM aggregation

# Optional
OPENAI_MODEL_NAME=gpt-4o-mini     # Optional (default: gpt-4o-mini)
GEMINI_MODEL_NAME=gemini-3-flash-preview  # Optional (default: gemini-3-flash-preview)
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
