import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import {
  getLatestHeadline,
  getLatestMarket,
  getLatestMomentum,
  type CompanyMomentum,
  type FunctionCount,
  type Headline,
  type TrendPoint,
} from "@/lib/data";

// A temporary page for migration step 7: two layout directions for the
// HiddenHire home page in the cobalt palette Meng picked, both built to
// look clearly different from Parrot (no centred hero, floating pill
// nav, pastel blobs, gradient headline, or floating bubbles). Meng
// picks one, then this page is deleted.

export const metadata: Metadata = {
  title: "Design options · HiddenHire",
  robots: { index: false },
};

const inter = Inter({ subsets: ["latin"] });

const BLUE = "#2563eb";
const NAVY = "#0b1b3a";
const UP = "#059669";

type Data = {
  headline: Headline | null;
  momentum: CompanyMomentum[];
  trend: TrendPoint[];
  functions: FunctionCount[];
};

export default async function DesignPage() {
  const [headline, momentum, market] = await Promise.all([
    getLatestHeadline(),
    getLatestMomentum(),
    getLatestMarket(),
  ]);
  const data: Data = {
    headline,
    momentum,
    trend: market?.trend ?? [],
    functions: market?.functions ?? [],
  };

  return (
    <div className={`${inter.className} bg-zinc-200`}>
      <Label id="d" text="D · Product split: headline on the left, a live preview of this week's movers on the right" />
      <ProductSplit data={data} />
      <Label id="e" text="E · Data briefing: a navy header with a market ticker, then a grid of live cards" />
      <DataBriefing data={data} />
    </div>
  );
}

function Label({ id, text }: { id: string; text: string }) {
  return (
    <div id={`label-${id}`} className="bg-zinc-900 px-4 py-3 text-sm text-zinc-100">
      {text}
    </div>
  );
}

// ---------------------------------------------------------------------
// Shared pieces
// ---------------------------------------------------------------------

function fmt(value: number) {
  return value.toLocaleString("en-US");
}

function signed(value: number) {
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${fmt(Math.abs(value))}`;
}

function shortDate(value: string) {
  const date = new Date(value.slice(0, 10) + "T12:00:00Z");
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

function topMovers(momentum: CompanyMomentum[], count: number) {
  return momentum.filter((row) => (row.net_change ?? 0) > 0).slice(0, count);
}

function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill={dark ? "#ffffff" : BLUE} />
        <circle cx="14.5" cy="14.5" r="6" fill="none" stroke={dark ? BLUE : "#fff"} strokeWidth="2.6" />
        <path d="M19 19l5 5" stroke={dark ? BLUE : "#fff"} strokeWidth="2.6" strokeLinecap="round" />
        <path d="M14.5 11.5v6M11.5 14.5h6" stroke={dark ? BLUE : "#fff"} strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      <span className={`text-[17px] font-semibold tracking-tight ${dark ? "text-white" : "text-[#0b1b3a]"}`}>
        HiddenHire
      </span>
    </span>
  );
}

function Sparkline({ values, color, width = 84, height = 26 }: {
  values: number[];
  color: string;
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
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function AreaChart({ trend, color, dark = false }: { trend: TrendPoint[]; color: string; dark?: boolean }) {
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
  const fillId = `area-${dark ? "dark" : "light"}`;
  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="h-36 w-full" aria-hidden="true">
        <defs>
          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity="0.28" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill={`url(#${fillId})`} />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className={`mt-2 flex justify-between text-xs ${dark ? "text-slate-400" : "text-slate-500"}`}>
        <span>{shortDate(trend[0].snapshot_date)}</span>
        <span>{shortDate(trend[trend.length - 1].snapshot_date)}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// D · Product split
// ---------------------------------------------------------------------

function ProductSplit({ data }: { data: Data }) {
  const { headline, momentum } = data;
  const movers = topMovers(momentum, 5);
  const weekChange =
    headline?.previous_open_roles != null ? headline.open_roles - headline.previous_open_roles : null;

  return (
    <section id="option-d" className="bg-white text-[#0b1b3a]">
      {/* Full-width top bar */}
      <header className="border-b border-slate-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Logo />
          <nav className="hidden items-center gap-8 text-[15px] text-slate-600 md:flex">
            <span>Find roles</span>
            <span>Company momentum</span>
            <span>Market insights</span>
            <span>Methodology</span>
          </nav>
          <span className="rounded-lg px-4 py-2 text-sm font-semibold text-white" style={{ background: BLUE }}>
            Find my matches
          </span>
        </div>
      </header>

      <div className="relative overflow-hidden">
        {/* Faint graph-paper grid, fading out toward the left */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(#e7edf8 1px, transparent 1px), linear-gradient(90deg, #e7edf8 1px, transparent 1px)",
            backgroundSize: "36px 36px",
            maskImage: "linear-gradient(90deg, transparent 0%, black 55%)",
          }}
        />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 lg:grid-cols-[1.05fr_1fr] lg:py-24">
          {/* Left: words */}
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em]" style={{ color: BLUE }}>
              NYC startup hiring · updated {headline ? shortDate(headline.latest_date) : "weekly"}
            </p>
            <h1 className="mt-5 text-[2.6rem] font-bold leading-[1.08] tracking-tight sm:text-6xl">
              Find the startups{" "}
              <span className="relative whitespace-nowrap">
                <span className="relative z-10">hiring for you</span>
                <span className="absolute inset-x-0 bottom-1 z-0 h-3 rounded-sm bg-blue-100 sm:bottom-2 sm:h-4" />
              </span>
              , before everyone else.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
              HiddenHire tracks the career pages of {headline?.companies ?? 43} emerging New York
              startups every week and ranks openings by your fit and each company&apos;s
              hiring momentum.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-lg px-5 py-3 font-semibold text-white shadow-sm" style={{ background: BLUE }}>
                Find my matches →
              </span>
              <span className="rounded-lg border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-700">
                See who&apos;s hiring
              </span>
            </div>
            {headline && (
              <dl className="mt-10 flex flex-wrap gap-x-8 gap-y-4 border-t border-slate-200 pt-6">
                <InlineStat label="startups tracked" value={fmt(headline.companies)} />
                <InlineStat
                  label="open roles"
                  value={fmt(headline.open_roles)}
                  note={weekChange != null ? `${signed(weekChange)} this week` : undefined}
                />
                <InlineStat label="new this week" value={headline.new_roles != null ? fmt(headline.new_roles) : "—"} />
              </dl>
            )}
          </div>

          {/* Right: a product preview built from real data */}
          <div className="relative">
            <div className="rounded-2xl border border-slate-200 bg-white shadow-[0_24px_60px_-20px_rgba(11,27,58,0.25)]">
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                <div>
                  <div className="font-semibold">Fastest-growing this week</div>
                  <div className="text-sm text-slate-500">Open roles across the last {data.trend.length} snapshots</div>
                </div>
                <span className="flex items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Live data
                </span>
              </div>
              <ul>
                {movers.map((row, index) => (
                  <li key={row.company_id} className="flex items-center gap-4 border-b border-slate-100 px-5 py-3 last:border-0">
                    <span className="w-4 text-sm font-semibold text-slate-400">{index + 1}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{row.company_name}</span>
                      <span className="text-sm text-slate-500">{fmt(row.open_now)} open roles</span>
                    </span>
                    <Sparkline values={row.trend} color={BLUE} />
                    <span className="w-12 text-right text-sm font-semibold tabular-nums" style={{ color: UP }}>
                      {signed(row.net_change ?? 0)}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="border-t border-slate-100 px-5 py-3 text-right text-sm font-semibold" style={{ color: BLUE }}>
                See all {momentum.length} companies →
              </div>
            </div>
            {/* A second, smaller card overlapping the first card's footer */}
            {headline?.new_roles != null && (
              <div className="absolute -bottom-24 -left-6 hidden w-52 rounded-xl border border-slate-200 bg-white p-4 shadow-[0_16px_40px_-16px_rgba(11,27,58,0.3)] sm:block">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">This week</div>
                <div className="mt-1 text-2xl font-bold tabular-nums">{fmt(headline.new_roles)} new</div>
                <div className="text-sm text-slate-500">{fmt(headline.closed_roles ?? 0)} closed</div>
                <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-slate-100">
                  <span
                    className="h-full"
                    style={{
                      background: BLUE,
                      width: `${(100 * headline.new_roles) / (headline.new_roles + (headline.closed_roles ?? 0))}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* How it works strip */}
      <div className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:grid-cols-3">
          <Step number="01" title="Tracked every Monday" text="Public job boards from Ashby, Greenhouse, and Lever, saved as weekly snapshots." />
          <Step number="02" title="Scored for you" text="Each role gets a fit score against your target roles, level, skills, and location." />
          <Step number="03" title="Ranked by momentum" text="Companies adding roles fastest, relative to their size, rise to the top." />
        </div>
      </div>
    </section>
  );
}

function InlineStat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div>
      <dt className="sr-only">{label}</dt>
      <dd className="text-2xl font-bold tabular-nums">{value}</dd>
      <dd className="text-sm text-slate-500">
        {label}
        {note && <span className="ml-1.5 font-medium" style={{ color: UP }}>{note}</span>}
      </dd>
    </div>
  );
}

function Step({ number, title, text }: { number: string; title: string; text: string }) {
  return (
    <div>
      <div className="text-sm font-semibold tabular-nums" style={{ color: BLUE }}>{number}</div>
      <div className="mt-2 font-semibold">{title}</div>
      <p className="mt-1 text-slate-600">{text}</p>
    </div>
  );
}

// ---------------------------------------------------------------------
// E · Data briefing
// ---------------------------------------------------------------------

function DataBriefing({ data }: { data: Data }) {
  const { headline, momentum, trend, functions } = data;
  const movers = topMovers(momentum, 4);
  const ticker = momentum.filter((row) => row.net_change != null && row.net_change !== 0).slice(0, 10);
  const shownFunctions = functions.filter((row) => row.function !== "Other").slice(0, 5);
  const maxFunction = Math.max(1, ...shownFunctions.map((row) => row.open_now));

  return (
    <section id="option-e" className="bg-slate-50 text-[#0b1b3a]">
      {/* Navy header block */}
      <div className="relative overflow-hidden text-white" style={{ background: `linear-gradient(160deg, ${NAVY} 0%, #102a5c 100%)` }}>
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <header className="relative mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
          <Logo dark />
          <nav className="hidden items-center gap-8 text-[15px] text-slate-300 md:flex">
            <span>Find roles</span>
            <span>Momentum</span>
            <span>Insights</span>
            <span>Methodology</span>
          </nav>
          <span className="rounded-lg bg-white px-4 py-2 text-sm font-semibold" style={{ color: NAVY }}>
            Find my matches
          </span>
        </header>

        {/* Market ticker, like a news band under the menu */}
        <div className="relative border-y border-white/10 bg-black/20">
          <div className="mx-auto flex max-w-6xl items-center gap-8 overflow-hidden whitespace-nowrap px-4 py-2.5 text-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-300">This week</span>
            {ticker.map((row) => (
              <span key={row.company_id} className="text-slate-300">
                {row.company_name}{" "}
                <span className={`font-semibold tabular-nums ${(row.net_change ?? 0) > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {(row.net_change ?? 0) > 0 ? "▲" : "▼"} {Math.abs(row.net_change ?? 0)}
                </span>
              </span>
            ))}
          </div>
        </div>

        <div className="relative mx-auto max-w-6xl px-4 pb-28 pt-12 sm:pt-16">
          <p className="text-sm font-medium text-blue-300">
            Week of {headline ? shortDate(headline.latest_date) : "—"} · {headline?.companies ?? 43} NYC startups
          </p>
          <h1 className="mt-4 max-w-3xl text-[2.6rem] font-bold leading-[1.08] tracking-tight sm:text-6xl">
            Find the startups hiring for you, <span className="text-blue-300">before everyone else.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
            A weekly read on which emerging New York startups are adding roles, ranked by your
            fit and each company&apos;s hiring momentum.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-lg px-5 py-3 font-semibold text-white" style={{ background: BLUE }}>
              Find my matches →
            </span>
            <span className="rounded-lg border border-white/25 px-5 py-3 font-semibold text-white">
              Read this week&apos;s briefing
            </span>
          </div>
        </div>
      </div>

      {/* Card grid, pulled up over the navy block */}
      <div className="relative mx-auto -mt-16 grid max-w-6xl gap-4 px-4 pb-16 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm text-slate-500">Open roles across tracked startups</div>
              <div className="mt-1 text-3xl font-bold tabular-nums">{headline ? fmt(headline.open_roles) : "—"}</div>
            </div>
            {headline?.previous_open_roles != null && (
              <span className="rounded-md bg-emerald-50 px-2 py-1 text-sm font-semibold text-emerald-700">
                {signed(headline.open_roles - headline.previous_open_roles)} vs last week
              </span>
            )}
          </div>
          <div className="mt-4">
            <AreaChart trend={trend} color={BLUE} />
          </div>
        </Card>

        <Card>
          <div className="text-sm text-slate-500">Growing fastest</div>
          <ul className="mt-3 space-y-3">
            {movers.map((row) => (
              <li key={row.company_id} className="flex items-center justify-between gap-3">
                <span className="min-w-0">
                  <span className="block truncate font-medium">{row.company_name}</span>
                  <span className="text-sm text-slate-500">{fmt(row.open_now)} open</span>
                </span>
                <Sparkline values={row.trend} color={BLUE} width={64} />
                <span className="w-10 text-right text-sm font-semibold tabular-nums" style={{ color: UP }}>
                  {signed(row.net_change ?? 0)}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <div className="text-sm text-slate-500">This week</div>
          <div className="mt-1 text-3xl font-bold tabular-nums">{headline?.new_roles != null ? fmt(headline.new_roles) : "—"}</div>
          <div className="text-slate-500">new roles posted, {fmt(headline?.closed_roles ?? 0)} closed</div>
          {headline?.new_roles != null && (
            <div className="mt-5 flex h-2.5 overflow-hidden rounded-full bg-rose-100">
              <span
                className="h-full"
                style={{
                  background: BLUE,
                  width: `${(100 * headline.new_roles) / (headline.new_roles + (headline.closed_roles ?? 0))}%`,
                }}
              />
            </div>
          )}
          <div className="mt-4 text-sm text-slate-500">
            {headline?.companies_growing ?? 0} companies grew · {headline?.companies_slowing ?? 0} slowed
          </div>
        </Card>

        <Card>
          <div className="text-sm text-slate-500">Open roles by function</div>
          <ul className="mt-3 space-y-2.5">
            {shownFunctions.map((row) => (
              <li key={row.function}>
                <div className="flex justify-between text-sm">
                  <span className="truncate">{row.function}</span>
                  <span className="tabular-nums text-slate-500">{fmt(row.open_now)}</span>
                </div>
                <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                  <div className="h-full rounded-full" style={{ background: BLUE, width: `${(100 * row.open_now) / maxFunction}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="flex flex-col justify-between" style={{ background: BLUE }}>
          <div className="text-white">
            <div className="text-lg font-semibold">Which of these fit you?</div>
            <p className="mt-1 text-blue-100">
              Pick your target roles and level. HiddenHire ranks every open role in seconds.
            </p>
          </div>
          <span className="mt-5 inline-block self-start rounded-lg bg-white px-4 py-2.5 font-semibold" style={{ color: BLUE }}>
            Find my matches →
          </span>
        </Card>
      </div>
    </section>
  );
}

function Card({
  className = "",
  style,
  children,
}: {
  className?: string;
  style?: React.CSSProperties;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_-20px_rgba(11,27,58,0.25)] ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}
