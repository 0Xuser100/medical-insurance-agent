"use client";

import { useTranslations } from "next-intl";
import { UploadZone } from "@/components/features/upload/UploadZone";

export default function HomePage() {
  const t = useTranslations("upload");

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="mt-2 text-sm text-muted">{t("subtitle")}</p>
      </div>
      <UploadZone />
    </div>
  );
}
