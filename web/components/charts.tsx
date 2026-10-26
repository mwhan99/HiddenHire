import { useId } from "react";

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

export type ChartPoint = { date: string; value: number };

// An area chart of one value over the weekly snapshots. `fromZero` starts
// the scale at 0, which suits small numbers (one company's open roles);
// otherwise the scale hugs the data to show week-to-week movement.
export function AreaChart({
  points,
  noun = "open roles",
  color = "#2563eb",
  fromZero = false,
}: {
  points: ChartPoint[];
  noun?: string;
  color?: string;
  fromZero?: boolean;
}) {
  const gradientId = useId();
  if (points.length < 2) return null;
  const values = points.map((point) => point.value);
  const min = fromZero ? 0 : Math.min(...values) * 0.97;
  const max = Math.max(...values) * (fromZero ? 1.1 : 1.01) || 1;
  const width = 600;
  const height = 160;
  const xy = values.map((value, index) => [
    (index / (values.length - 1)) * width,
    height - ((value - min) / (max - min || 1)) * height,
  ]);
  const line = xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `0,${height} ${line} ${width},${height}`;
  const first = points[0];
  const last = points[points.length - 1];
  const summary =
    `${noun[0].toUpperCase()}${noun.slice(1)} went from ${fmt(first.value)} on ${shortDate(first.date)} ` +
    `to ${fmt(last.value)} on ${shortDate(last.date)}, across ${points.length} weekly snapshots.`;

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
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.28" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill={`url(#${gradientId})`} />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <figcaption className="mt-2 flex justify-between text-xs text-slate-500">
        <span>{shortDate(first.date)}</span>
        <span>{shortDate(last.date)}</span>
      </figcaption>
    </figure>
  );
}
