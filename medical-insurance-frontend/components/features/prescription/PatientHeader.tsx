"use client";

import { useTranslations } from "next-intl";
import { displayOrFallback } from "@/lib/utils/formatters";
import type { PatientProfile } from "@/lib/schemas/validation";

interface PatientHeaderProps {
  patient: PatientProfile;
}

export function PatientHeader({ patient }: PatientHeaderProps) {
  const t = useTranslations("result");
  const ct = useTranslations("common");

  const initials = patient.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

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
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        {t("patientInfo")}
      </h2>
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-purple-100 text-lg font-bold text-purple-700">
          {initials}
        </div>
        <div>
          <p className="text-lg font-bold text-foreground">
            {displayOrFallback(patient.name)}
          </p>
          <p className="text-sm text-muted">
            ID: {displayOrFallback(patient.id)}
          </p>
          <div className="mt-1 flex gap-2">
            <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-foreground">
              {displayOrFallback(patient.age)} {ct("years")}
            </span>
            <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-foreground">
              {displayOrFallback(patient.gender)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
