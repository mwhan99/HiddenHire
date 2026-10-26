import { fmt, signed } from "@/lib/format";

// Horizontal bars with a count and, optionally, the week's change.
export function BarList({
  items,
}: {
  items: { label: string; value: number; change?: number }[];
}) {
  const max = Math.max(1, ...items.map((item) => item.value));
  return (
    <ul className="space-y-2.5">
      {items.map((item) => (
        <li key={item.label}>
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className="truncate">{item.label}</span>
            <span className="flex shrink-0 items-baseline gap-2 tabular-nums">
              <span className="text-slate-600">{fmt(item.value)}</span>
              {item.change !== undefined && (
                <span
                  className={`w-9 text-right text-xs font-semibold ${
                    item.change > 0 ? "text-up" : item.change < 0 ? "text-rose-600" : "text-slate-400"
                  }`}
                >
                  {signed(item.change)}
                </span>
              )}
            </span>
          </div>
          <div className="mt-1 h-1.5 rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-brand" style={{ width: `${(100 * item.value) / max}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}
