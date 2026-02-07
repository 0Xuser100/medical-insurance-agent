<!--
SYNC IMPACT REPORT - Constitution Update
=========================================
Version Change: [NEW CONSTITUTION] → 1.0.0
Modified Principles: N/A (Initial creation)
Added Sections:
  - Core Principles (5 principles)
  - Security & Compliance Requirements
  - Development Standards
  - Governance
Templates Requiring Updates:
  ✅ plan-template.md - Reviewed, aligned with principles
  ✅ spec-template.md - Reviewed, aligned with user story prioritization
  ✅ tasks-template.md - Reviewed, aligned with test-first and independent stories
Follow-up TODOs: None
=========================================
-->

# Medical Insurance Validation API Constitution

## Core Principles

### I. AI-First with Structured Output
**The system MUST prioritize structured, schema-enforced AI outputs over unstructured responses.**

All AI interactions (OCR extraction, validation logic, reasoning) must produce Pydantic-validated JSON schemas. Use native structured output capabilities (e.g., Gemini's structured output, LangChain with schemas) rather than prompt-based JSON requests followed by parsing. This ensures:
- Type safety at the API boundary
- Predictable error handling
- Contract-based integration testing
- No hallucinated field names or malformed responses

**Rationale**: Medical data requires precision. Structured outputs eliminate parsing errors and enable compile-time validation of AI responses, critical for healthcare applications where data integrity is non-negotiable.

### II. Bilingual & Accessibility by Default
**Every user-facing message, validation reason, and error response MUST include both English and Arabic.**

- All rejection reasons, approval messages, and UI badges must provide parallel EN/AR content
- API responses must include both `reason_en` and `reason_ar` fields
- Frontend components must support RTL (right-to-left) rendering for Arabic
- No English-only fallback in production; missing translations are bugs

**Rationale**: Healthcare services in bilingual regions must ensure equal access. Providing Arabic alongside English is not an enhancement—it's a compliance and accessibility requirement.

### III. Async-First Architecture
**All I/O-bound operations (file uploads, AI calls, database queries) MUST use async/await patterns.**

- FastAPI endpoints must be `async def`
- External API calls (Gemini, OpenAI) must use async clients
- File operations must use `aiofiles`
- Job processing must be non-blocking (background tasks or async queues)
- No blocking `requests`, `open()`, or synchronous SDK calls in the hot path

**Rationale**: Medical prescription validation involves multiple slow operations (OCR, AI inference, file I/O). Async architecture prevents request blocking, enables horizontal scaling, and improves throughput under load.

### IV. Testability & Contract Validation
**Every feature MUST have contract tests verifying API schemas before implementation begins.**

- Write contract tests (schema validation) first, before any implementation
- Integration tests for multi-step workflows (upload → extract → validate → result)
- Mock external dependencies (Gemini API) in tests to ensure reproducibility
- Test both success and failure paths (malformed inputs, API errors, edge cases)
- No "we'll add tests later"—tests are the specification

**Rationale**: Healthcare APIs cannot fail silently or return malformed data. Contract tests ensure the API surface remains stable and predictable, even as internal implementations change (e.g., CrewAI → LangChain migration).

### V. Observability & Auditability
**Every decision, validation rule, and AI inference MUST be logged with structured metadata.**

- Use structured logging (Loguru with JSON) for all AI decisions
- Include transaction IDs, timestamps, and confidence scores in responses
- Log validation rule outcomes (clinical match, medication limit, duration check)
- Provide audit trails: who/what/when for every prescription processed
- No silent failures; errors must be surfaced with actionable context

**Rationale**: Medical systems require full audit trails for regulatory compliance. Every prescription validation decision must be traceable, explainable, and verifiable by human reviewers.

## Security & Compliance Requirements

### Data Privacy
- Uploaded prescription files MUST be stored securely with access controls
- Patient data (name, age, diagnosis) MUST NOT be logged in plaintext
- API keys (Gemini, OpenAI) MUST be environment variables, never hardcoded
- File uploads MUST enforce size limits (10MB) and allowed MIME types

### Error Handling
- API errors MUST NOT expose internal implementation details (no stack traces in production)
- Validation failures MUST provide actionable error messages in both languages
- HTTP status codes MUST follow REST conventions (400 for bad input, 500 for server errors)
- Failed AI calls MUST return graceful fallback responses, not crash the service

### Rate Limiting & Abuse Prevention
- API endpoints MUST implement rate limiting per client/IP (to be enforced in production)
- File upload validation MUST prevent malicious files (type checking, size limits)
- Job queues MUST have timeouts to prevent resource exhaustion

## Development Standards

### Code Organization
- Follow SOLID principles: dependency injection via `api/dependencies.py`
- Use protocol classes (`core/protocols.py`) for interface definitions
- Group by feature domain (`services/`, `models/`, `api/`) not by layer
- Keep prompts separate (`prompts/aggregator_prompt.py`) for easy iteration

### Testing Discipline
- Contract tests in `tests/contract/` (API schema validation)
- Integration tests in `tests/integration/` (multi-step workflows)
- Unit tests in `tests/unit/` (isolated logic, if applicable)
- Use pytest with `pytest-asyncio` for async test support

### Documentation
- API endpoints documented via OpenAPI/Swagger (FastAPI auto-generation)
- Inline docstrings for complex validation logic (ICD-10 mapping, fuzzy matching)
- README must include quickstart, architecture diagram, and example flows
- Keep `LLM_AGGREGATOR_README.md` up-to-date with validation pipeline changes

### Version Control
- Use semantic versioning: MAJOR.MINOR.PATCH
- Git commit messages must follow Conventional Commits (feat:, fix:, docs:, chore:)
- Feature branches must include issue/feature number (e.g., `123-add-duration-check`)
- No commits directly to `main`; all changes via pull requests

## Governance

### Amendment Procedure
1. Propose constitution changes via GitHub issue with rationale
2. Discuss impact on existing features and templates
3. Update dependent templates (plan, spec, tasks) in same PR
4. Increment version (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
5. Document in Sync Impact Report (HTML comment at top of this file)

### Compliance Review
- All pull requests MUST reference relevant constitution principles
- Breaking a principle requires explicit justification in PR description
- Reviewers MUST verify tests exist and pass before merge
- Constitution violations without justification block merge

### Versioning Policy
- **MAJOR**: Removal or redefinition of a core principle (e.g., removing bilingual requirement)
- **MINOR**: New principle added or material expansion of existing (e.g., adding performance benchmarks)
- **PATCH**: Clarifications, typo fixes, wording improvements (no semantic change)

**Version**: 1.0.0 | **Ratified**: 2026-02-07 | **Last Amended**: 2026-02-07
