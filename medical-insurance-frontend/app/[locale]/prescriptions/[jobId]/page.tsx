"use client";

import { use } from "react";
import { useTranslations } from "next-intl";
import { useJobResult } from "@/lib/api/queries";
import { ResultCard } from "@/components/features/prescription/ResultCard";
import { PatientHeader } from "@/components/features/prescription/PatientHeader";
import { MedicationCard } from "@/components/features/prescription/MedicationCard";
import { DiagnosisCard } from "@/components/features/prescription/DiagnosisCard";
import { LabsCard } from "@/components/features/prescription/LabsCard";
import { ProviderCard } from "@/components/features/prescription/ProviderCard";
import { ResultSkeleton } from "@/components/features/prescription/ResultSkeleton";

export default function PrescriptionResultPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = use(params);
  const t = useTranslations("result");
  const et = useTranslations("error");
  const { data, isLoading, error } = useJobResult(jobId);

  if (isLoading) {
    return <ResultSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">
            {et("title")}
          </p>
          <p className="mt-2 text-sm text-muted">
            {et("jobNotFound")}
          </p>
        </div>
      </div>
    );
  }

  const result = data.result;
  const extracted = data.extracted_data;

  if (!result) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center p-6">
        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">
            {et("title")}
          </p>
          <p className="mt-2 text-sm text-muted">
            {et("jobNotFound")}
          </p>
        </div>
      </div>
    );
  }

  const medications = result.ai_validation_engine.line_items.filter(
    (item) => item.type === "MEDICATION",
  );
  const labs = result.ai_validation_engine.line_items.filter(
    (item) => item.type === "LAB_ANALYSIS",
  );

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Overall Result Summary */}
      <ResultCard result={result} />

      {/* Patient Information */}
      <PatientHeader patient={result.patient_profile} />

      {/* Diagnosis (from extracted data) */}
      {extracted?.diagnosis && (
        <DiagnosisCard diagnosis={extracted.diagnosis} />
      )}

      {/* Medication Validation */}
      {medications.length > 0 && (
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3" />
            </svg>
            {t("medicationTitle")}
          </h2>
          <div className="space-y-4">
            {medications.map((item, idx) => (
              <MedicationCard key={idx} item={item} />
            ))}
          </div>
        </section>
      )}

      {/* Lab Analysis Items */}
      {labs.length > 0 && (
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            {t("labTitle")}
          </h2>
          <div className="space-y-4">
            {labs.map((item, idx) => (
              <MedicationCard key={idx} item={item} />
            ))}
          </div>
        </section>
      )}

      {/* Extracted Labs Table */}
      {extracted?.labs && extracted.labs.length > 0 && (
        <LabsCard labs={extracted.labs} />
      )}

      {/* Provider Information */}
      {extracted?.provider && (
        <ProviderCard provider={extracted.provider} />
      )}
    </div>
  );
}
