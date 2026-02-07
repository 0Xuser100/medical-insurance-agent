import { cn } from "@/lib/utils/cn";

interface StatusBadgeProps {
  status: "APPROVED" | "REJECTED";
  label: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span
      role="status"
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold",
        status === "APPROVED"
          ? "bg-green-100 text-green-800"
          : "bg-red-100 text-red-800",
      )}
    >
      {status === "APPROVED" ? "✓" : "✕"} {label}
    </span>
  );
}

interface RiskBadgeProps {
  level: "LOW" | "MEDIUM" | "HIGH";
  label: string;
}

export function RiskBadge({ level, label }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        level === "LOW" && "bg-green-50 text-green-700",
        level === "MEDIUM" && "bg-yellow-50 text-yellow-700",
        level === "HIGH" && "bg-red-50 text-red-700",
      )}
    >
      {label}
    </span>
  );
}
