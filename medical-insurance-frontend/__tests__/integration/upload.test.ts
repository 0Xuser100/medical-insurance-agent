import { describe, it, expect } from "vitest";
import { UploadResponseSchema } from "@/lib/schemas/validation";
import { parseError } from "@/lib/errors";
import { ZodError } from "zod/v4";

/**
 * Integration test: verify that a realistic backend upload response
 * passes frontend Zod validation end-to-end.
 */

describe("Upload Integration", () => {
  it("validates a realistic backend upload response", () => {
    // Simulated response exactly as FastAPI serialises UploadResponse
    const backendResponse = {
      job_id: "a3f2c8b1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      status: "UPLOADED",
      filename: "prescription_scan.jpg",
      file_size: 245768,
      created_at: "2026-02-07T14:23:45.123456",
      message: "File uploaded successfully",
    };

    const result = UploadResponseSchema.safeParse(backendResponse);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.filename).toBe("prescription_scan.jpg");
      expect(result.data.file_size).toBe(245768);
      expect(result.data.message).toBe("File uploaded successfully");
    }
  });

  it("rejects the OLD incorrect schema shape (started_at, completed_at, error)", () => {
    const oldShapeResponse = {
      job_id: "a3f2c8b1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      status: "UPLOADED",
      created_at: "2026-02-07T14:23:45.123456",
      started_at: null,
      completed_at: null,
      error: null,
    };

    const result = UploadResponseSchema.safeParse(oldShapeResponse);
    expect(result.success).toBe(false);
  });

  it("handles a minimal valid response", () => {
    const minimal = {
      job_id: "test-id",
      status: "UPLOADED",
      filename: "a.png",
      file_size: 1,
      created_at: "2026-01-01T00:00:00",
      message: "ok",
    };

    const result = UploadResponseSchema.safeParse(minimal);
    expect(result.success).toBe(true);
  });
});

describe("Error Handling", () => {
  it("classifies ZodError as VALIDATION_ERROR", () => {
    // Trigger a real ZodError by parsing invalid data
    const result = UploadResponseSchema.safeParse({ bad: "data" });
    expect(result.success).toBe(false);

    if (!result.success) {
      const parsed = parseError(result.error);
      expect(parsed.type).toBe("VALIDATION_ERROR");
    }
  });

  it("classifies TypeError with fetch message as NETWORK_ERROR", () => {
    const err = new TypeError("Failed to fetch");
    const parsed = parseError(err);
    expect(parsed.type).toBe("NETWORK_ERROR");
  });

  it("classifies generic Error with detail as API_ERROR", () => {
    const err = new Error("Invalid file type. Allowed: image/jpeg, image/png");
    const parsed = parseError(err);
    expect(parsed.type).toBe("API_ERROR");
    expect(parsed.type === "API_ERROR" && parsed.detail).toBeTruthy();
  });

  it("classifies unknown values as UNKNOWN_ERROR", () => {
    const parsed = parseError(42);
    expect(parsed.type).toBe("UNKNOWN_ERROR");
  });
});
