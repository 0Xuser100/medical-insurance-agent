export function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function formatConfidence(score: string): string {
  const num = parseFloat(score);
  if (isNaN(num)) return score;
  return `${(num * 100).toFixed(0)}%`;
}

export function displayOrFallback(
  value: string | null | undefined,
  fallback = "—",
): string {
  if (!value || value === "not found") return fallback;
  return value;
}
