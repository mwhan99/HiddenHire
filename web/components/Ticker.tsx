import type { CompanyMomentum } from "@/lib/data";

// A slowly scrolling band of this week's changes in open roles, like a
// market ticker. The list is drawn twice so the scroll loops seamlessly;
// the copy is hidden from screen readers. It stands still for visitors
// who ask their system for reduced motion, and pauses on hover.
export function Ticker({ rows }: { rows: CompanyMomentum[] }) {
  const changed = rows.filter((row) => row.net_change != null && row.net_change !== 0);
  if (changed.length === 0) return null;

  const items = (hidden: boolean) => (
    <ul className="flex shrink-0 items-center gap-8 pr-8" aria-hidden={hidden || undefined}>
      {changed.map((row) => {
        const change = row.net_change ?? 0;
        return (
          <li key={row.company_id} className="text-slate-300">
            {row.company_name}{" "}
            <span className={`font-semibold tabular-nums ${change > 0 ? "text-emerald-400" : "text-rose-400"}`}>
              <span aria-hidden="true">{change > 0 ? "▲" : "▼"}</span>
              <span className="sr-only">{change > 0 ? "up" : "down"}</span> {Math.abs(change)}
            </span>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="ticker relative border-y border-white/10 bg-black/20">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-2.5 text-sm">
        <span className="shrink-0 text-xs font-semibold uppercase tracking-wider text-blue-300">
          This week
        </span>
        <div className="relative min-w-0 flex-1 overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_4%,black_96%,transparent)]">
          <div className="animate-ticker flex w-max whitespace-nowrap pl-4">
            {items(false)}
            {items(true)}
          </div>
        </div>
      </div>
    </div>
  );
}
