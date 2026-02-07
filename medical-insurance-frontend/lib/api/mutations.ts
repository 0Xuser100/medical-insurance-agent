import { useMutation } from "@tanstack/react-query";
import { apiFetch, API_URL } from "./client";
import {
  UploadResponseSchema,
  type UploadResponse,
} from "@/lib/schemas/validation";
import { parseError } from "@/lib/errors";

export function useUploadPrescription() {
  return useMutation<UploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Upload failed");
      }

      const data = await res.json();
      return UploadResponseSchema.parse(data);
    },
    onError: (error) => {
      const parsed = parseError(error);
      if (parsed.type === "VALIDATION_ERROR") {
        console.error("[Schema Drift] Upload response validation failed:", parsed.issues);
      }
    },
  });
}

export function useProcessJob() {
  return useMutation<{ job_id: string; status: string }, Error, string>({
    mutationFn: async (jobId: string) => {
      return apiFetch("/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
    },
  });
}
