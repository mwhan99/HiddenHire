import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { BarList } from "@/components/BarList";
import { Card } from "@/components/Card";
import { AreaChart } from "@/components/charts";
import { PageHeader } from "@/components/PageHeader";
import { getLatestBriefing, type Briefing, type Mover } from "@/lib/data";
import { fmt, shortDate, shortIndustry, signed } from "@/lib/format";

export const metadata: Metadata = {
  title: "Market insights",
  description:
    "This week's hiring briefing across tracked New York startups: open, new and closed roles, " +
    "the fastest-growing and slowing companies, and roles by function and industry.",
};

// Market Insights: the week's numbers that are the same for every visitor,
// all precalculated by market_insights.py and saved by supabase_sync.py.

export default async function InsightsPage() {
  const briefing = await getLatestBriefing();
  if (!briefing) {
    return (
      <main>
        <PageHeader active="/insights" eyebrow="Market insights" title="This week's hiring briefing" />
        <p className="mx-auto max-w-6xl px-4 py-12 text-slate-600">No snapshots have been saved yet.</p>
      </main>
    );
  }

  const { headline, growing, slowing, functions, industries, trend } = briefing;
  const compared = headline.previous_date != null;
  const weekChange = compared ? headline.open_roles - (headline.previous_open_roles ?? 0) : null;

  return (
    <main>
      <PageHeader
        active="/insights"
        eyebrow={`Market insights · week of ${shortDate(headline.latest_date)}`}
        title="This week's hiring briefing"
        description={
          compared ? (
            <>
              Comparing {shortDate(headline.latest_date)} with {shortDate(headline.previous_date!)} (
              {headline.gap_days} days apart) across {headline.companies} tracked New York startups.
            </>
          ) : (
            "Week-over-week comparisons start once a second weekly snapshot exists."
          )
        }
      />

      <div className="mx-auto max-w-6xl space-y-4 px-4 py-10">
        {/* Headline numbers */}
        <section aria-label="Headline numbers" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat
            label="Open roles"
            value={fmt(headline.open_roles)}
            note={weekChange != null ? <Change value={weekChange} suffix=" vs last week" /> : "First snapshot"}
          />
          <Stat label="New this week" value={headline.new_roles != null ? fmt(headline.new_roles) : "—"} note="postings that weren't open last week" />
          <Stat label="Closed this week" value={headline.closed_roles != null ? fmt(headline.closed_roles) : "—"} note="postings that came down" />
          <Stat
            label="Companies"
            value={`${headline.companies_growing ?? 0} grew`}
            note={`${headline.companies_slowing ?? 0} slowed, out of ${headline.companies}`}
          />
        </section>

        {/* Findings and trend */}
        <section className="grid gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-2">
            <h2 className="font-semibold">Key findings</h2>
            <ul className="mt-3 space-y-3 text-slate-700">
              {findings(briefing).map((finding, index) => (
                <li key={index} className="flex gap-3 leading-relaxed">
                  <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                  <span>{finding}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card className="lg:col-span-3">
            <h2 className="text-sm font-normal text-slate-500">Open roles at each weekly snapshot</h2>
            <p className="mt-1 text-3xl font-bold tabular-nums">{fmt(headline.open_roles)}</p>
            <div className="mt-4">
              <AreaChart points={trend.map((point) => ({ date: point.snapshot_date, value: point.open_roles }))} />
            </div>
            <p className="mt-3 text-xs text-slate-400">A new snapshot is added every Monday.</p>
          </Card>
        </section>

        {/* Movers */}
        <section className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="font-semibold">Fastest-growing companies</h2>
            <p className="text-sm text-slate-500">Ranked by net change relative to company size</p>
            {growing.length ? <MoverTable rows={growing} /> : <Empty>No company added open roles this week.</Empty>}
          </Card>
          <Card>
            <h2 className="font-semibold">Slowing down</h2>
            <p className="text-sm text-slate-500">Largest drops relative to company size</p>
            {slowing.length ? <MoverTable rows={slowing} /> : <Empty>No company reduced its open roles this week.</Empty>}
          </Card>
        </section>

        {/* Breakdowns */}
        <section className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="font-semibold">Open roles by job function</h2>
            <p className="mb-4 text-sm text-slate-500">Assigned from job titles by keyword</p>
            <BarList items={functions.map((row) => ({ label: row.function, value: row.open_now, change: compared ? row.net_change : undefined }))} />
          </Card>
          <Card>
            <h2 className="font-semibold">Open roles by industry</h2>
            <p className="mb-4 text-sm text-slate-500">
              A startup with several industry tags counts toward each, so this doesn&apos;t add up to the total
            </p>
            <BarList items={industries.map((row) => ({ label: row.industry, value: row.open_now, change: compared ? row.net_change : undefined }))} />
          </Card>
        </section>

        <p className="max-w-3xl pt-2 text-sm leading-relaxed text-slate-500">
          &ldquo;Size&rdquo; means a company&apos;s open roles in the earlier snapshot, counting
          smaller companies as 10, the same adjustment Hiring Momentum uses. See the{" "}
          <Link href="/methodology" className="font-medium text-brand hover:text-blue-500">methodology</Link>{" "}
          for details, or{" "}
          <Link href="/companies" className="font-medium text-brand hover:text-blue-500">every company&apos;s momentum</Link>.
        </p>
      </div>
    </main>
  );
}

// A few plain-language sentences built from this week's numbers.
function findings({ headline, growing, functions, industries }: Briefing): ReactNode[] {
  const result: ReactNode[] = [];
  if (headline.previous_open_roles != null && headline.previous_open_roles > 0) {
    const change = headline.open_roles - headline.previous_open_roles;
    const pct = Math.abs((100 * change) / headline.previous_open_roles).toFixed(1);
    result.push(
      change === 0 ? (
        <>Open roles held steady at <b>{fmt(headline.open_roles)}</b>.</>
      ) : (
        <>
          Open roles {change > 0 ? "rose" : "fell"} <b>{pct}%</b> to <b>{fmt(headline.open_roles)}</b>, with{" "}
          {fmt(headline.new_roles ?? 0)} new postings and {fmt(headline.closed_roles ?? 0)} closed.
        </>
      ),
    );
  }
  const largest = functions.find((row) => row.function !== "Other");
  const gainer = [...functions].filter((row) => row.function !== "Other").sort((a, b) => b.net_change - a.net_change)[0];
  if (largest) {
    result.push(
      gainer && gainer.net_change > 0 && gainer.function !== largest.function ? (
        <>
          <b>{largest.function}</b> is the biggest function ({fmt(largest.open_now)} roles), while{" "}
          <b>{gainer.function}</b> added the most this week ({signed(gainer.net_change)}).
        </>
      ) : (
        <>
          <b>{largest.function}</b> is the biggest function, with {fmt(largest.open_now)} open roles
          {largest.net_change > 0 ? ` (${signed(largest.net_change)} this week)` : ""}.
        </>
      ),
    );
  }
  const topIndustry = industries[0];
  if (topIndustry && headline.open_roles > 0) {
    result.push(
      <>
        Startups tagged <b>{topIndustry.industry}</b> account for {fmt(topIndustry.open_now)} open roles,{" "}
        {Math.round((100 * topIndustry.open_now) / headline.open_roles)}% of the total.
      </>,
    );
  }
  const fastest = growing[0];
  const biggest = [...growing].sort((a, b) => b.net_change - a.net_change)[0];
  if (fastest) {
    result.push(
      biggest && biggest.company_id !== fastest.company_id ? (
        <>
          <b>{fastest.company}</b> grew fastest for its size ({signed(fastest.net_change)} on{" "}
          {fmt(fastest.previous_open)} openings); <b>{biggest.company}</b> added the most roles (
          {signed(biggest.net_change)}).
        </>
      ) : (
        <>
          <b>{fastest.company}</b> grew fastest, adding {signed(fastest.net_change)} roles on{" "}
          {fmt(fastest.previous_open)} openings.
        </>
      ),
    );
  }
  return result;
}

function MoverTable({ rows }: { rows: Mover[] }) {
  return (
    <table className="mt-4 w-full text-left text-sm">
      <thead className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
        <tr>
          <th scope="col" className="py-2 pr-3 font-semibold">Company</th>
          <th scope="col" className="px-3 py-2 text-right font-semibold">Open</th>
          <th scope="col" className="px-3 py-2 text-right font-semibold">Change</th>
          <th scope="col" className="hidden py-2 pl-3 text-right font-semibold sm:table-cell">New / closed</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {rows.map((row) => (
          <tr key={row.company_id}>
            <td className="py-2.5 pr-3">
              <Link href={`/companies/${row.company_id}`} className="font-medium text-ink hover:text-brand">
                {row.company}
              </Link>
              <div className="text-xs text-slate-500">{shortIndustry(row.industry)}</div>
            </td>
            <td className="px-3 py-2.5 text-right tabular-nums">{fmt(row.open_now)}</td>
            <td className="px-3 py-2.5 text-right">
              <Change value={row.net_change} />
              <div className="text-xs tabular-nums text-slate-500">
                {row.change_pct > 0 ? "+" : row.change_pct < 0 ? "−" : ""}
                {Math.abs(Math.round(row.change_pct))}%
              </div>
            </td>
            <td className="hidden py-2.5 pl-3 text-right tabular-nums text-slate-600 sm:table-cell">
              {fmt(row.new_roles)} / {fmt(row.closed_roles)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Change({ value, suffix = "" }: { value: number; suffix?: string }) {
  const color = value > 0 ? "text-up" : value < 0 ? "text-rose-600" : "text-slate-500";
  return (
    <span className={`font-semibold tabular-nums ${color}`}>
      {signed(value)}
      {suffix && <span className="font-normal text-slate-500">{suffix}</span>}
    </span>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: ReactNode }) {
  return (
    <Card>
      <h2 className="text-sm font-normal text-slate-500">{label}</h2>
      <p className="mt-1 text-2xl font-bold tabular-nums sm:text-3xl">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{note}</p>
    </Card>
  );
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="mt-4 text-slate-500">{children}</p>;
}
