import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useJobStatus } from "@/lib/api/queries";
import React from "react";

/**
 * Integration test: verify job status polling uses the correct endpoint
 *
 * This test ensures that the frontend polls job status using GET /result/{job_id}
 * and NOT the incorrect GET /job/{job_id} endpoint (which would return 405).
 */

// Mock the apiFetch client
vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
  API_URL: "http://localhost:8000",
}));

describe("Job Status Polling Endpoint", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should use /result/{job_id} endpoint for job status polling", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const mockApiFetch = vi.mocked(apiFetch);

    // Mock successful response from /result/{job_id}
    mockApiFetch.mockResolvedValueOnce({
      job_id: "PAT-0b1f01e6dc5f",
      status: "VALIDATING",
      created_at: "2026-02-07T18:37:55.000Z",
      started_at: "2026-02-07T18:37:56.000Z",
      completed_at: null,
      error: "Processing... Current stage: VALIDATING",
      extracted_data: null,
      result: null,
    });

    const { result } = renderHook(() => useJobStatus("PAT-0b1f01e6dc5f"), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Verify the correct endpoint was called
    expect(mockApiFetch).toHaveBeenCalledWith("/result/PAT-0b1f01e6dc5f");

    // Verify it was NOT called with the old incorrect endpoint
    expect(mockApiFetch).not.toHaveBeenCalledWith("/job/PAT-0b1f01e6dc5f");
  });

  it("should NOT call /job/{job_id} endpoint (which would return 405)", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const mockApiFetch = vi.mocked(apiFetch);

    mockApiFetch.mockResolvedValueOnce({
      job_id: "PAT-test123456",
      status: "PROCESSING",
      created_at: "2026-02-07T18:00:00.000Z",
      started_at: "2026-02-07T18:00:01.000Z",
      completed_at: null,
      error: "Processing... Current stage: PROCESSING",
      extracted_data: null,
      result: null,
    });

    renderHook(() => useJobStatus("PAT-test123456"), { wrapper });

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalled();
    });

    // Get all calls to apiFetch
    const calls = mockApiFetch.mock.calls;

    // Assert NO calls were made to /job/ endpoint
    const incorrectEndpointCalls = calls.filter(
      (call) => call[0].includes("/job/")
    );
    expect(incorrectEndpointCalls).toHaveLength(0);

    // Assert at least one call was made to /result/ endpoint
    const correctEndpointCalls = calls.filter(
      (call) => call[0].includes("/result/")
    );
    expect(correctEndpointCalls.length).toBeGreaterThan(0);
  });

  it("should poll using /result/ for all job statuses", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const mockApiFetch = vi.mocked(apiFetch);

    const statuses = [
      "UPLOADED",
      "PROCESSING",
      "EXTRACTING",
      "VALIDATING",
      "AGGREGATING",
      "COMPLETED",
      "FAILED",
    ];

    for (const status of statuses) {
      mockApiFetch.mockClear();
      mockApiFetch.mockResolvedValueOnce({
        job_id: `PAT-${status.toLowerCase()}`,
        status: status,
        created_at: "2026-02-07T18:00:00.000Z",
        started_at: "2026-02-07T18:00:01.000Z",
        completed_at: status === "COMPLETED" || status === "FAILED"
          ? "2026-02-07T18:00:10.000Z"
          : null,
        error: status === "FAILED" ? "Test error" : null,
        extracted_data: null,
        result: null,
      });

      const { result } = renderHook(
        () => useJobStatus(`PAT-${status.toLowerCase()}`),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Verify correct endpoint for this status
      expect(mockApiFetch).toHaveBeenCalledWith(
        `/result/PAT-${status.toLowerCase()}`
      );
    }
  });

  it("should handle completed status correctly with /result/ endpoint", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const mockApiFetch = vi.mocked(apiFetch);

    mockApiFetch.mockResolvedValueOnce({
      job_id: "PAT-completed123",
      status: "COMPLETED",
      created_at: "2026-02-07T18:37:55.000Z",
      started_at: "2026-02-07T18:37:56.000Z",
      completed_at: "2026-02-07T18:38:18.000Z",
      error: null,
      extracted_data: {
        patient: { name: "Test Patient", age: "30", gender: "Male", id: "P123" },
        provider: { name: "Dr. Test", id: "D123", facility: "Test Clinic" },
        diagnosis: { primary: "Test Diagnosis", icd_code: "A00.0" },
        medications: [],
        labs: [],
        date: "2026-02-07",
      },
      result: null,
    });

    const { result } = renderHook(() => useJobStatus("PAT-completed123"), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/result/PAT-completed123");
    expect(result.current.data?.status).toBe("COMPLETED");
    expect(result.current.data?.completed_at).not.toBeNull();
  });
});
