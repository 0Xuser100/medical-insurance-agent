"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils/cn";
import { formatConfidence, formatTimestamp } from "@/lib/utils/formatters";
import { StatusBadge } from "./StatusBadge";
import type { ValidationResult } from "@/lib/schemas/validation";

interface ResultCardProps {
  result: ValidationResult;
}

export function ResultCard({ result }: ResultCardProps) {
  const t = useTranslations("result");
  const engine = result.ai_validation_engine;

  const approvedCount = engine.line_items.filter(
    (i) => i.status === "APPROVED",
  ).length;
  const rejectedCount = engine.line_items.filter(
    (i) => i.status === "REJECTED",
  ).length;

  function getOverallMessage(): string {
    if (engine.overall_status === "APPROVED") {
      return t("overallApproved");
    }
    if (approvedCount === 0) {
      return t("overallRejected", { count: engine.medication_count });
    }
    return t("overallPartial", {
      approved: approvedCount,
      rejected: rejectedCount,
    });
  }

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      {/* Top row: status + badge */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-foreground">
            {t("title")}
          </h2>
          <p className="mt-1 text-sm text-muted">{t("scannedFrom")}</p>
        </div>
        <StatusBadge
          status={engine.overall_status}
          label={
            engine.overall_status === "APPROVED"
              ? t("approved")
              : t("rejected")
          }
        />
      </div>

      {/* AI Summary */}
      <div
        className={cn(
          "mt-4 rounded-lg p-4",
          engine.overall_status === "APPROVED"
            ? "bg-green-50 text-green-800"
            : "bg-red-50 text-red-800",
        )}
      >
        <p className="text-sm font-medium">{getOverallMessage()}</p>
      </div>

      {/* Stats grid */}
      <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatItem
          label={t("confidenceScore")}
          value={formatConfidence(engine.confidence_score)}
        />
        <StatItem
          label={t("medicationCount")}
          value={engine.medication_count}
        />
        <StatItem label={t("transactionId")} value={result.transaction_id} />
        <StatItem
          label={t("timestamp")}
          value={formatTimestamp(result.timestamp)}
        />
      </div>
    </div>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
        {label}
      </p>
      <p className="mt-0.5 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}
