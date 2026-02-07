import { describe, it, expect } from "vitest";
import { UploadResponseSchema } from "@/lib/schemas/validation";

/**
 * Contract test: UploadResponseSchema must match the backend UploadResponse.
 *
 * Backend fields (src/models/schemas.py UploadResponse):
 *   job_id, status, filename, file_size, created_at, message
 */

const VALID_UPLOAD_RESPONSE = {
  job_id: "550e8400-e29b-41d4-a716-446655440000",
  status: "UPLOADED",
  filename: "prescription_scan.jpg",
  file_size: 245768,
  created_at: "2026-02-07T14:23:45.123456",
  message: "File uploaded successfully",
};

describe("UploadResponseSchema", () => {
  it("validates a correct backend upload response", () => {
    const result = UploadResponseSchema.safeParse(VALID_UPLOAD_RESPONSE);
    expect(result.success).toBe(true);
  });

  it("requires the filename field", () => {
    const { filename: _, ...withoutFilename } = VALID_UPLOAD_RESPONSE;
    const result = UploadResponseSchema.safeParse(withoutFilename);
    expect(result.success).toBe(false);
  });

  it("requires the file_size field", () => {
    const { file_size: _, ...withoutFileSize } = VALID_UPLOAD_RESPONSE;
    const result = UploadResponseSchema.safeParse(withoutFileSize);
    expect(result.success).toBe(false);
  });

  it("requires the message field", () => {
    const { message: _, ...withoutMessage } = VALID_UPLOAD_RESPONSE;
    const result = UploadResponseSchema.safeParse(withoutMessage);
    expect(result.success).toBe(false);
  });

  it("rejects non-numeric file_size", () => {
    const result = UploadResponseSchema.safeParse({
      ...VALID_UPLOAD_RESPONSE,
      file_size: "large",
    });
    expect(result.success).toBe(false);
  });

  it("accepts all valid JobStatus values for upload", () => {
    for (const status of ["UPLOADED", "EXTRACTING", "VALIDATING", "COMPLETED", "FAILED"]) {
      const result = UploadResponseSchema.safeParse({
        ...VALID_UPLOAD_RESPONSE,
        status,
      });
      expect(result.success).toBe(true);
    }
  });

  it("rejects an invalid status value", () => {
    const result = UploadResponseSchema.safeParse({
      ...VALID_UPLOAD_RESPONSE,
      status: "INVALID_STATUS",
    });
    expect(result.success).toBe(false);
  });
});
