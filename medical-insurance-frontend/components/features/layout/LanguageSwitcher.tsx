"use client";

import { useLocale } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { useTransition } from "react";
import { cn } from "@/lib/utils/cn";

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  function switchTo(newLocale: "en" | "ar") {
    startTransition(() => {
      router.replace(pathname, { locale: newLocale });
    });
  }

  return (
    <div className="flex items-center gap-1 rounded-lg border border-border p-1">
      <button
        onClick={() => switchTo("en")}
        disabled={isPending}
        aria-label="Switch to English"
        className={cn(
          "rounded-md px-3 py-1 text-sm font-medium transition-colors",
          locale === "en"
            ? "bg-primary text-primary-foreground"
            : "text-muted hover:text-foreground",
        )}
      >
        EN
      </button>
      <button
        onClick={() => switchTo("ar")}
        disabled={isPending}
        aria-label="التبديل إلى العربية"
        className={cn(
          "rounded-md px-3 py-1 text-sm font-medium transition-colors",
          locale === "ar"
            ? "bg-primary text-primary-foreground"
            : "text-muted hover:text-foreground",
        )}
      >
        AR
      </button>
    </div>
  );
}
