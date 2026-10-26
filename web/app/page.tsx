import Link from "next/link";

import { Card } from "@/components/Card";
import { AreaChart, Sparkline } from "@/components/charts";
import { SiteHeader } from "@/components/SiteHeader";
import { Ticker } from "@/components/Ticker";
import { getLatestHeadline, getLatestMarket, getLatestMomentum } from "@/lib/data";
import { fmt, longDate, nextMonday, shortDate, signed } from "@/lib/format";

// The home page ("Data briefing" layout): a navy header with this week's
// ticker and headline, then a grid of live cards. Every number comes from
// Supabase through cached functions, so the page is prebuilt and
// refreshed about once an hour.

const STEPS = [
  {
    title: "Tracked every Monday",
    text: "Public job boards from Ashby, Greenhouse, and Lever are saved as weekly snapshots, so changes show up week over week.",
  },
  {
    title: "Scored for you",
    text: "Each opening gets a fit score against your target roles, experience level, skills, industries, and location.",
  },
  {
    title: "Ranked by momentum",
    text: "Companies adding roles fastest, relative to their size, rise to the top, with a plain-language reason for every match.",
  },
];

export default async function HomePage() {
  const [headline, momentum, market] = await Promise.all([
    getLatestHeadline(),
    getLatestMomentum(),
    getLatestMarket(),
  ]);
  const trend = market?.trend ?? [];
  const functions = (market?.functions ?? []).filter((row) => row.function !== "Other").slice(0, 5);
  const maxFunction = Math.max(1, ...functions.map((row) => row.open_now));
  const movers = momentum.filter((row) => (row.net_change ?? 0) > 0).slice(0, 4);
  const weekChange =
    headline?.previous_open_roles != null ? headline.open_roles - headline.previous_open_roles : null;
  const newShare =
    headline?.new_roles != null && headline.new_roles + (headline.closed_roles ?? 0) > 0
      ? (100 * headline.new_roles) / (headline.new_roles + (headline.closed_roles ?? 0))
      : null;

  return (
    <main>
      {/* Navy header block */}
      <section className="relative overflow-hidden bg-gradient-to-br from-navy to-navy-2 text-white">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <SiteHeader />
        <Ticker rows={momentum} />

        <div className="relative mx-auto max-w-6xl px-4 pb-28 pt-12 sm:pt-16">
          <p className="text-sm font-medium text-blue-300">
            {headline
              ? `Week of ${shortDate(headline.latest_date)} · ${headline.companies} NYC startups`
              : "Weekly hiring signals from NYC startups"}
          </p>
          <h1 className="mt-4 max-w-3xl text-[2.6rem] font-bold leading-[1.08] tracking-tight sm:text-6xl">
            Find the startups hiring for you, <span className="text-blue-300">before everyone else.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
            A weekly read on which emerging New York startups are adding roles, ranked by your fit
            and each company&apos;s hiring momentum.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/search"
              className="rounded-lg bg-brand px-5 py-3 font-semibold text-white transition-colors hover:bg-blue-500"
            >
              Find my matches →
            </Link>
            <Link
              href="/insights"
              className="rounded-lg border border-white/25 px-5 py-3 font-semibold text-white transition-colors hover:bg-white/10"
            >
              Read this week&apos;s briefing
            </Link>
          </div>
        </div>
      </section>

      {/* Live cards, pulled up over the navy block */}
      <section aria-label="This week's numbers" className="relative mx-auto -mt-16 grid max-w-6xl gap-4 px-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-sm font-normal text-slate-500">Open roles across tracked startups</h2>
              <p className="mt-1 text-3xl font-bold tabular-nums">{headline ? fmt(headline.open_roles) : "—"}</p>
            </div>
            {weekChange != null && (
              <span className="rounded-md bg-emerald-50 px-2 py-1 text-sm font-semibold text-emerald-700">
                {signed(weekChange)} vs last week
              </span>
            )}
          </div>
          <div className="mt-4">
            <AreaChart points={trend.map((point) => ({ date: point.snapshot_date, value: point.open_roles }))} />
          </div>
        </Card>

        <Card className="flex flex-col">
          <h2 className="text-sm font-normal text-slate-500">Growing fastest</h2>
          <ul className="mt-3 flex-1 space-y-3">
            {movers.map((row) => (
              <li key={row.company_id} className="flex items-center justify-between gap-3">
                <span className="min-w-0">
                  <Link href={`/companies/${row.company_id}`} className="block truncate font-medium hover:text-brand">{row.company_name}</Link>
                  <span className="text-sm text-slate-500">{fmt(row.open_now)} open roles</span>
                </span>
                <Sparkline values={row.trend} width={64} />
                <span className="w-10 text-right text-sm font-semibold tabular-nums text-up">
                  {signed(row.net_change ?? 0)}
                </span>
              </li>
            ))}
          </ul>
          <Link href="/companies" className="mt-4 text-sm font-semibold text-brand hover:text-blue-500">
            See all {momentum.length} companies →
          </Link>
        </Card>

        <Card className="flex flex-col">
          <h2 className="text-sm font-normal text-slate-500">This week</h2>
          <p className="mt-1 text-3xl font-bold tabular-nums">
            {headline?.new_roles != null ? fmt(headline.new_roles) : "—"}
          </p>
          <p className="text-slate-500">
            new roles posted
            {headline?.closed_roles != null && `, ${fmt(headline.closed_roles)} closed`}
          </p>
          {newShare != null && (
            <div
              className="mt-5 flex h-2.5 overflow-hidden rounded-full bg-rose-100"
              role="img"
              aria-label={`${fmt(headline?.new_roles ?? 0)} new roles and ${fmt(headline?.closed_roles ?? 0)} closed roles`}
            >
              <span className="h-full bg-brand" style={{ width: `${newShare}%` }} />
            </div>
          )}
          <p className="mt-4 text-sm text-slate-500">
            {headline?.companies_growing ?? 0} companies grew · {headline?.companies_slowing ?? 0} slowed
          </p>
          {headline && (
            <p className="mt-auto pt-4 text-xs text-slate-400">
              Updated {longDate(headline.latest_date)} · next update {shortDate(nextMonday(headline.latest_date))}
            </p>
          )}
        </Card>

        <Card>
          <h2 className="text-sm font-normal text-slate-500">Open roles by function</h2>
          <ul className="mt-3 space-y-2.5">
            {functions.map((row) => (
              <li key={row.function}>
                <div className="flex justify-between gap-3 text-sm">
                  <span className="truncate">{row.function}</span>
                  <span className="tabular-nums text-slate-500">{fmt(row.open_now)}</span>
                </div>
                <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand" style={{ width: `${(100 * row.open_now) / maxFunction}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <div className="flex flex-col justify-between rounded-2xl bg-brand p-5 text-white shadow-[0_12px_40px_-20px_rgba(37,99,235,0.6)]">
          <div>
            <h2 className="text-lg font-semibold">Which of these fit you?</h2>
            <p className="mt-1 text-blue-100">
              Pick your target roles and experience level. HiddenHire ranks every open role at
              these startups in seconds.
            </p>
          </div>
          <Link
            href="/search"
            className="mt-5 self-start rounded-lg bg-white px-4 py-2.5 font-semibold text-brand transition-colors hover:bg-blue-50"
          >
            Find my matches →
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:py-20">
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">How HiddenHire works</h2>
        <ol className="mt-8 grid gap-8 sm:grid-cols-3">
          {STEPS.map((step, index) => (
            <li key={step.title}>
              <span className="text-sm font-semibold tabular-nums text-brand">0{index + 1}</span>
              <h3 className="mt-2 font-semibold">{step.title}</h3>
              <p className="mt-1 leading-relaxed text-slate-600">{step.text}</p>
            </li>
          ))}
        </ol>
        <Link href="/methodology" className="mt-8 inline-block font-semibold text-brand hover:text-blue-500">
          Read the full methodology →
        </Link>
      </section>
    </main>
  );
}
