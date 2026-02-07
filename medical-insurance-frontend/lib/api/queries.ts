import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import {
  JobResultResponseSchema,
  type JobResultResponse,
} from "@/lib/schemas/validation";

export function useJobResult(jobId: string | null) {
  return useQuery<JobResultResponse>({
    queryKey: ["job-result", jobId],
    queryFn: async () => {
      const data = await apiFetch(`/result/${jobId}`);
      return JobResultResponseSchema.parse(data);
    },
    enabled: !!jobId,
  });
}

export function useJobStatus(jobId: string | null) {
  return useQuery<JobResultResponse>({
    queryKey: ["job-status", jobId],
    queryFn: async () => {
      const data = await apiFetch(`/result/${jobId}`);
      return JobResultResponseSchema.parse(data);
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "COMPLETED" || status === "FAILED") return false;
      return 3000; // Poll every 3 seconds while processing
    },
  });
}
