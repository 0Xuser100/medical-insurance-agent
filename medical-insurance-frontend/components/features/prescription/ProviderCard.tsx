"use client";

import { useTranslations } from "next-intl";
import { displayOrFallback } from "@/lib/utils/formatters";
import type { Provider } from "@/lib/schemas/validation";

interface ProviderCardProps {
  provider: Provider;
}

export function ProviderCard({ provider }: ProviderCardProps) {
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
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        {t("providerTitle")}
      </h2>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted">Name</span>
          <span className="font-medium text-foreground">
            {displayOrFallback(provider.name)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted">ID</span>
          <span className="font-medium text-foreground">
            {displayOrFallback(provider.id)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted">Facility</span>
          <span className="font-medium text-foreground">
            {displayOrFallback(provider.facility)}
          </span>
        </div>
      </div>
    </div>
  );
}
