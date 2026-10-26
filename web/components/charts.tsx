import type { TrendPoint } from "@/lib/data";
import { fmt, shortDate } from "@/lib/format";

// Small hand-drawn SVG charts. No chart library is needed for shapes this
// simple, which keeps the page light.

export function Sparkline({
  values,
  color = "#2563eb",
  width = 84,
  height = 26,
}: {
  values: number[];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - 2 - ((value - min) / span) * (height - 4);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true" className="shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function AreaChart({ trend, color = "#2563eb" }: { trend: TrendPoint[]; color?: string }) {
  if (trend.length < 2) return null;
  const values = trend.map((point) => point.open_roles);
  const min = Math.min(...values) * 0.97;
  const max = Math.max(...values) * 1.01;
  const width = 600;
  const height = 160;
  const xy = values.map((value, index) => [
    (index / (values.length - 1)) * width,
    height - ((value - min) / (max - min)) * height,
  ]);
  const line = xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `0,${height} ${line} ${width},${height}`;
  const first = trend[0];
  const last = trend[trend.length - 1];
  const summary =
    `Open roles went from ${fmt(first.open_roles)} on ${shortDate(first.snapshot_date)} ` +
    `to ${fmt(last.open_roles)} on ${shortDate(last.snapshot_date)}, across ${trend.length} weekly snapshots.`;

  return (
    <figure>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-36 w-full"
        role="img"
        aria-label={summary}
      >
        <defs>
          <linearGradient id="open-roles-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.28" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#open-roles-fill)" />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <figcaption className="mt-2 flex justify-between text-xs text-slate-500">
        <span>{shortDate(first.snapshot_date)}</span>
        <span>{shortDate(last.snapshot_date)}</span>
      </figcaption>
    </figure>
  );
}
