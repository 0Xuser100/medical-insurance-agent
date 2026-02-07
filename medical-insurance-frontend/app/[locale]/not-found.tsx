import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function NotFound() {
  const t = useTranslations("error");

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
          <span className="text-2xl font-bold text-muted">404</span>
        </div>
        <h2 className="text-lg font-bold text-foreground">{t("notFound")}</h2>
        <p className="mt-2 text-sm text-muted">
          {t("notFoundDescription")}
        </p>
        <Link
          href="/"
          className="mt-4 inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          {t("goHome")}
        </Link>
      </div>
    </div>
  );
}
