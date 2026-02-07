export function ResultSkeleton() {
  return (
    <div className="mx-auto max-w-4xl animate-pulse space-y-6 p-6">
      {/* Header skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="h-5 w-48 rounded bg-gray-200" />
            <div className="h-4 w-32 rounded bg-gray-200" />
          </div>
          <div className="h-7 w-24 rounded-full bg-gray-200" />
        </div>
        <div className="mt-4 h-12 rounded-lg bg-gray-100" />
        <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-1">
              <div className="h-3 w-16 rounded bg-gray-200" />
              <div className="h-4 w-24 rounded bg-gray-200" />
            </div>
          ))}
        </div>
      </div>

      {/* Patient skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="h-4 w-32 rounded bg-gray-200" />
        <div className="mt-4 flex items-center gap-4">
          <div className="h-14 w-14 rounded-full bg-gray-200" />
          <div className="space-y-2">
            <div className="h-5 w-36 rounded bg-gray-200" />
            <div className="h-4 w-24 rounded bg-gray-200" />
          </div>
        </div>
      </div>

      {/* Medication cards skeleton */}
      {Array.from({ length: 2 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-3">
              <div className="h-5 w-32 rounded bg-gray-200" />
              <div className="flex gap-2">
                <div className="h-6 w-20 rounded-full bg-gray-200" />
                <div className="h-6 w-20 rounded-full bg-gray-200" />
              </div>
            </div>
            <div className="h-10 w-10 rounded-full bg-gray-200" />
          </div>
          <div className="mt-4 h-16 rounded-lg bg-gray-100" />
        </div>
      ))}
    </div>
  );
}
