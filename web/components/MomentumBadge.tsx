import type { MomentumLabel } from "@/lib/data";

// Colour and symbol for each Company Momentum label. The thresholds live
// in market_insights.py (size-adjusted weekly growth of ±5%).
export const MOMENTUM_STYLES: Record<MomentumLabel, { icon: string; className: string; help: string }> = {
  Growing: {
    icon: "▲",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    help: "Open roles grew by at least 5% of company size this week.",
  },
  Steady: {
    icon: "●",
    className: "bg-slate-100 text-slate-700 ring-slate-200",
    help: "Open roles changed by less than 5% of company size this week.",
  },
  Slowing: {
    icon: "▼",
    className: "bg-rose-50 text-rose-700 ring-rose-200",
    help: "Open roles fell by at least 5% of company size this week.",
  },
  "New to tracking": {
    icon: "✦",
    className: "bg-blue-50 text-blue-700 ring-blue-200",
    help: "No openings in last week's snapshot, so there is no change to compare yet.",
  },
};

export const MOMENTUM_LABELS = Object.keys(MOMENTUM_STYLES) as MomentumLabel[];

export function MomentumBadge({ label }: { label: MomentumLabel }) {
  const style = MOMENTUM_STYLES[label];
  return (
    <span
      title={style.help}
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${style.className}`}
    >
      <span aria-hidden="true">{style.icon}</span>
      {label}
    </span>
  );
}
