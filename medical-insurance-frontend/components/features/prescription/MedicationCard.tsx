"use client";

import { useLocale, useTranslations } from "next-intl";
import { cn } from "@/lib/utils/cn";
import { StatusBadge, RiskBadge } from "./StatusBadge";
import type { LineItem } from "@/lib/schemas/validation";

interface MedicationCardProps {
  item: LineItem;
}

export function MedicationCard({ item }: MedicationCardProps) {
  const t = useTranslations("result");
  const locale = useLocale();
  const reason =
    locale === "ar"
      ? item.validation_details.reason_ar
      : item.validation_details.reason_en;

  return (
    <div
      className={cn(
        "rounded-xl border p-5 transition-colors",
        item.status === "APPROVED"
          ? "border-green-200 bg-green-50/50"
          : "border-red-200 bg-red-50/50",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">
              {item.item_name}
            </h3>
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-muted">
              {item.type === "MEDICATION" ? "Rx" : "Lab"}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <StatusBadge
              status={item.status}
              label={
                item.status === "APPROVED" ? t("approved") : t("rejected")
              }
            />
            <RiskBadge
              level={item.risk_level}
              label={
                item.risk_level === "HIGH"
                  ? t("riskHigh")
                  : item.risk_level === "MEDIUM"
                    ? t("riskMedium")
                    : t("riskLow")
              }
            />
          </div>
        </div>

        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg",
            item.status === "APPROVED"
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700",
          )}
        >
          {item.status === "APPROVED" ? "✓" : "✕"}
        </div>
      </div>

      {/* AI Reason */}
      <div className="mt-4 rounded-lg bg-white/80 p-3">
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted">
          {t("aiInsight")}
        </p>
        <p className="text-sm leading-relaxed text-foreground">{reason}</p>
      </div>

      {/* Validation details row */}
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted">
        <span>
          Clinical Match:{" "}
          <span
            className={cn(
              "font-medium",
              item.validation_details.clinical_match
                ? "text-green-700"
                : "text-red-700",
            )}
          >
            {item.validation_details.clinical_match ? "Yes" : "No"}
          </span>
        </span>
        {item.validation_details.duration_check && (
          <span>
            Duration: {item.validation_details.duration_check}
          </span>
        )}
      </div>
    </div>
  );
}
