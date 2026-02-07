"use client";

import { useTranslations } from "next-intl";
import { displayOrFallback } from "@/lib/utils/formatters";
import type { Diagnosis } from "@/lib/schemas/validation";

interface DiagnosisCardProps {
  diagnosis: Diagnosis;
}

export function DiagnosisCard({ diagnosis }: DiagnosisCardProps) {
  const t = useTranslations("result");

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M9 12h6M12 9v6M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
        {t("diagnosisTitle")}
      </h2>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted">Primary</span>
          <span className="font-medium text-foreground">
            {displayOrFallback(diagnosis.primary)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted">ICD Code</span>
          <span className="font-medium text-foreground">
            {displayOrFallback(diagnosis.icd_code)}
          </span>
        </div>
      </div>
    </div>
  );
}
