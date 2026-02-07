"use client";

import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { useJobStatus } from "@/lib/api/queries";
import { useProcessJob } from "@/lib/api/mutations";
import { cn } from "@/lib/utils/cn";
import type { JobStatus } from "@/lib/schemas/validation";

const STEPS: JobStatus[] = ["UPLOADED", "EXTRACTING", "VALIDATING", "COMPLETED"];

function getStepIndex(status: JobStatus): number {
  const idx = STEPS.indexOf(status);
  return idx === -1 ? 0 : idx;
}

export default function StatusPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const t = useTranslations("status");
  const et = useTranslations("error");
  const router = useRouter();
  const { data, isLoading, error } = useJobStatus(jobId);
  const processMutation = useProcessJob();

  if (!jobId) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <p className="text-sm text-muted">{et("jobNotFound")}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">{et("title")}</p>
          <p className="mt-2 text-sm text-muted">{et("networkError")}</p>
        </div>
      </div>
    );
  }

  const status = data.status;
  const currentStep = getStepIndex(status);
  const isFailed = status === "FAILED";
  const isCompleted = status === "COMPLETED";

  function getStatusLabel(s: JobStatus): string {
    const map: Record<JobStatus, string> = {
      UPLOADED: t("uploaded"),
      EXTRACTING: t("extracting"),
      VALIDATING: t("validating"),
      COMPLETED: t("completed"),
      FAILED: t("failed"),
    };
    return map[s];
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <div className="rounded-xl border border-border bg-card p-8">
        <h1 className="text-xl font-bold text-foreground">{t("title")}</h1>
        <p className="mt-1 text-xs text-muted">Job ID: {jobId}</p>

        {/* Progress Steps */}
        <div className="mt-8 space-y-6">
          {STEPS.map((step, idx) => {
            const isActive = idx === currentStep && !isFailed;
            const isDone = idx < currentStep || isCompleted;

            return (
              <div key={step} className="flex items-start gap-4">
                {/* Step circle */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition-colors",
                      isDone
                        ? "border-primary bg-primary text-primary-foreground"
                        : isActive
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-gray-50 text-muted",
                    )}
                  >
                    {isDone ? "✓" : idx + 1}
                  </div>
                  {idx < STEPS.length - 1 && (
                    <div
                      className={cn(
                        "mt-1 h-6 w-0.5",
                        isDone ? "bg-primary" : "bg-border",
                      )}
                    />
                  )}
                </div>

                {/* Step text */}
                <div className="pt-1">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      isDone || isActive
                        ? "text-foreground"
                        : "text-muted",
                    )}
                  >
                    {getStatusLabel(step)}
                  </p>
                  {isActive && !isCompleted && (
                    <div className="mt-1 flex items-center gap-2">
                      <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                      <span className="text-xs text-muted">Processing...</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Failed state */}
        {isFailed && (
          <div className="mt-6 rounded-lg bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">{t("failed")}</p>
            {data.error && (
              <p className="mt-1 text-xs text-red-600">{data.error}</p>
            )}
            <button
              onClick={() => processMutation.mutate(jobId)}
              disabled={processMutation.isPending}
              className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {t("retry")}
            </button>
          </div>
        )}

        {/* Completed — navigate to results */}
        {isCompleted && (
          <div className="mt-6">
            <button
              onClick={() => router.push(`/prescriptions/${jobId}`)}
              className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
            >
              {t("viewResults")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
