# Research Report: Schema Alignment & Validation Best Practices

**Feature**: Fix Photo Upload Schema Mismatch
**Research Date**: 2026-02-07
**Purpose**: Inform schema fix implementation with production-grade patterns

---

## Research Questions Addressed

1. **Zod Schema Flexibility**: Strict vs. passthrough vs. strip modes
2. **Contract Testing**: Alignment between Pydantic (backend) and Zod (frontend)
3. **Error Handling**: Distinguishing validation errors from network failures
4. **Backward Compatibility**: Handling schema evolution

---

## 1. Schema Validation Strategy

### Decision: Use Strict Mode with Explicit Fields

**Rationale**:
- The upload response schema is well-defined and stable
- Strict validation catches schema drift early (fail-fast)
- Better type safety for critical upload flow
- Contract tests will detect any backend changes

**Implementation**:
```typescript
export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  filename: z.string(),
  file_size: z.number(),
  created_at: z.string(),
  message: z.string(),
}); // Default strict mode
```

**Alternatives Considered**:
- **`.passthrough()`**: Rejected because upload response is stable and controlled by our backend
- **`.strip()`**: Default behavior, equivalent to strict for our use case since we define all expected fields

**Future-Proofing**:
- If backend adds optional fields, make them explicit in frontend schema with `.optional()`
- Contract tests will alert us to schema changes

---

## 2. Contract Testing Approach

### Decision: Runtime Validation Tests + Type Checking

**Rationale**:
- No OpenAPI generation setup yet (can be added later)
- Runtime tests validate actual API responses
- Type tests ensure schema matches domain types
- Simple to implement, no build process changes

**Implementation Plan**:

#### Backend Contract Tests
```python
# tests/contract/test_upload_schema.py
def test_upload_response_schema():
    """Verify UploadResponse matches documented contract."""
    response = UploadResponse(
        job_id="test-123",
        status=JobStatus.UPLOADED,
        filename="prescription.jpg",
        file_size=12345,
        created_at=datetime.now(),
        message="File uploaded successfully"
    )

    # Serialize to JSON (what frontend receives)
    json_data = response.model_dump_json()
    parsed = json.loads(json_data)

    # Verify all required fields present
    assert "job_id" in parsed
    assert "filename" in parsed
    assert "file_size" in parsed
    assert "message" in parsed
```

#### Frontend Integration Tests
```typescript
// tests/integration/upload.test.ts
it('validates upload response against schema', async () => {
  const response = await uploadPrescription(mockFile);

  // This will throw if schema doesn't match
  const validated = UploadResponseSchema.parse(response);

  expect(validated.filename).toBeDefined();
  expect(validated.file_size).toBeGreaterThan(0);
});
```

**Alternatives Considered**:
- **OpenAPI generation with orval**: Overkill for single schema fix, but recommended for future features
- **Snapshot testing**: Less useful for detecting specific field mismatches
- **Manual testing only**: Insufficient, schema drift would go undetected

---

## 3. Error Handling Pattern

### Decision: Discriminated Union with Centralized Error Parsing

**Rationale**:
- Clear distinction between error types (validation, network, API)
- Type-safe error handling in UI
- Better debugging with specific error context
- Follows React Query best practices

**Implementation**:

#### Error Type Definition
```typescript
// lib/errors.ts
export type AppError =
  | { type: 'VALIDATION_ERROR'; issues: z.ZodIssue[]; rawData: unknown }
  | { type: 'NETWORK_ERROR'; message: string; status?: number }
  | { type: 'API_ERROR'; message: string; code: string }
  | { type: 'UNKNOWN_ERROR'; error: unknown };

export function parseError(error: unknown): AppError {
  if (error instanceof z.ZodError) {
    return { type: 'VALIDATION_ERROR', issues: error.issues, rawData: error };
  }
  // ... network and API error detection
}
```

#### Usage in Mutation
```typescript
// lib/api/mutations.ts
export function useUploadPrescription() {
  return useMutation({
    mutationFn: async (file: File) => {
      const response = await uploadFile(file);
      // Throws ZodError if schema mismatch
      return UploadResponseSchema.parse(response);
    },
    onError: (error) => {
      const parsed = parseError(error);
      if (parsed.type === 'VALIDATION_ERROR') {
        console.error('Schema mismatch detected:', parsed.issues);
        // Alert: Backend schema may have changed
      }
    },
  });
}
```

**Alternatives Considered**:
- **Generic Error class**: Less type-safe, harder to handle specific cases
- **No error parsing**: Would mix validation errors with network errors (current bug)
- **Try-catch everywhere**: Repetitive, inconsistent error handling

---

## 4. Backward Compatibility Strategy

### Decision: Explicit Optional Fields (Not Passthrough)

**Rationale**:
- Backend is stable and under our control
- Explicit fields provide better type safety
- Contract tests alert us to changes
- Easy to add optional fields when backend evolves

**Implementation**:
```typescript
// Current schema (all required)
export const UploadResponseSchema = z.object({
  job_id: z.string(),
  status: JobStatusSchema,
  filename: z.string(),
  file_size: z.number(),
  created_at: z.string(),
  message: z.string(),
});

// If backend adds optional field in future:
export const UploadResponseSchema = z.object({
  // ... existing fields
  thumbnail_url: z.string().optional(), // NEW: explicitly optional
});
```

**Schema Evolution Guidelines**:
1. **Adding fields**: Make them `.optional()` initially
2. **Removing fields**: Deprecate in backend first, then remove from frontend
3. **Renaming fields**: Add new field as optional, deprecate old, migrate
4. **Type changes**: Create new schema version if breaking

**Alternatives Considered**:
- **`.passthrough()`**: Loses type safety, accepts any extra fields
- **Schema versioning**: Overkill for simple bug fix, but good for future major changes
- **Flexible parsing**: Would silently accept malformed responses (defeats purpose of validation)

---

## 5. Testing Strategy Summary

### Contract Tests (Backend)
**Location**: `tests/contract/test_upload_schema.py`
**Purpose**: Verify Pydantic schema serializes correctly
**Frequency**: Run on every backend change

### Integration Tests (Frontend)
**Location**: `medical-insurance-frontend/__tests__/lib/api/upload.test.ts`
**Purpose**: Validate actual API responses against Zod schema
**Frequency**: Run on every frontend change + CI/CD

### Unit Tests (Frontend)
**Location**: `medical-insurance-frontend/__tests__/lib/schemas/validation.test.ts`
**Purpose**: Test schema validation logic in isolation
**Frequency**: Run on every commit

---

## Key Decisions Summary

| Decision Point | Choice | Rationale |
|---------------|--------|-----------|
| Schema validation mode | Strict (default) | Fail-fast, type safety, controlled API |
| Contract testing | Runtime + Type tests | Simple, no build changes, catches drift |
| Error handling | Discriminated union | Type-safe, specific error messages |
| Backward compatibility | Explicit optional fields | Type safety over flexibility |
| Schema generation | Manual (for now) | Single fix, can automate later |

---

## Implementation Recommendations

1. **Update frontend schema** with three new fields: `filename`, `file_size`, `message`
2. **Remove incorrect fields**: `started_at`, `completed_at`, `error` (these belong to job status schema)
3. **Add contract tests** to prevent future schema mismatches
4. **Improve error handling** to distinguish validation errors from network errors
5. **Update UI component** to display filename and file size on success

---

## Future Considerations

### For Next Schema Changes
- Consider setting up OpenAPI generation with `orval` for automated schema sync
- Implement schema versioning if breaking changes become frequent
- Add E2E tests for complete upload → validation → result flow

### For Production
- Monitor for Zod validation errors in error tracking (Sentry, LogRocket)
- Set up alerts for schema validation failures (indicates backend change)
- Document schema in OpenAPI spec for API consumers

---

## References

- **Zod Documentation**: https://zod.dev/
- **React Query Error Handling**: https://tkdodo.eu/blog/react-query-error-handling
- **FastAPI + Next.js Templates**: https://github.com/vintasoftware/nextjs-fastapi-template
- **Type-Safe API Clients**: https://stevekinney.com/courses/full-stack-typescript/generating-zod-openapi

---

**Research Status**: ✅ Complete
**Ready for Phase 1**: Yes
**Open Questions**: None
