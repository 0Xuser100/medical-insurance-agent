import * as z from "zod/v4";

export type AppError =
  | { type: "VALIDATION_ERROR"; issues: z.core.$ZodIssue[]; rawData: unknown }
  | { type: "NETWORK_ERROR"; message: string; status?: number }
  | { type: "API_ERROR"; message: string; detail?: string }
  | { type: "UNKNOWN_ERROR"; error: unknown };

export function parseError(error: unknown): AppError {
  // Zod validation error (schema mismatch)
  if (error instanceof z.ZodError) {
    return {
      type: "VALIDATION_ERROR",
      issues: error.issues,
      rawData: error,
    };
  }

  // Network / fetch failure
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return {
      type: "NETWORK_ERROR",
      message: "Network request failed. Please check your connection.",
    };
  }

  // Our own Error with HTTP detail from the mutation handler
  if (error instanceof Error) {
    const msg = error.message;

    // API errors (thrown by mutationFn when !res.ok)
    if (msg && msg !== "Upload failed") {
      return { type: "API_ERROR", message: msg, detail: msg };
    }

    return { type: "NETWORK_ERROR", message: msg || "An unexpected error occurred." };
  }

  return { type: "UNKNOWN_ERROR", error };
}
