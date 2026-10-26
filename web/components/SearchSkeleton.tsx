// Grey placeholder blocks shown while search results load.
export function SearchSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-live="polite">
      <span className="sr-only">Finding your matches…</span>
      <div className="h-24 animate-pulse rounded-2xl bg-white shadow-sm" />
      <div className="h-7 w-64 animate-pulse rounded bg-slate-200" />
      {[0, 1, 2].map((index) => (
        <div key={index} className="h-56 animate-pulse rounded-2xl bg-white shadow-sm" />
      ))}
    </div>
  );
}
