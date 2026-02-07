"use client";

import { useTranslations } from "next-intl";
import { displayOrFallback } from "@/lib/utils/formatters";
import type { LabAnalysis } from "@/lib/schemas/validation";

interface LabsCardProps {
  labs: LabAnalysis[];
}

export function LabsCard({ labs }: LabsCardProps) {
  const t = useTranslations("result");

  if (labs.length === 0) return null;

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
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        {t("labTitle")}
      </h2>
      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left">
              <th className="px-4 py-2 font-medium text-muted">
                {t("labName")}
              </th>
              <th className="px-4 py-2 font-medium text-muted">
                {t("labType")}
              </th>
            </tr>
          </thead>
          <tbody>
            {labs.map((lab, idx) => (
              <tr key={idx} className="border-t border-border">
                <td className="px-4 py-2 font-medium text-foreground">
                  {displayOrFallback(lab.name)}
                </td>
                <td className="px-4 py-2 text-muted">
                  {displayOrFallback(lab.type)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
