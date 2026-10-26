import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { Card } from "@/components/Card";
import { AreaChart } from "@/components/charts";
import { MOMENTUM_STYLES, MomentumBadge } from "@/components/MomentumBadge";
import { PageHeader } from "@/components/PageHeader";
import { getCompanyDetail, getLatestMomentum, getSnapshotDates, type CompanyDetail } from "@/lib/data";
import { fmt, shortDate, shortIndustry, signed } from "@/lib/format";
import { pageMetadata } from "@/lib/site";

// One page per company, e.g. /companies/C024. Every company in the latest
// snapshot is prebuilt; a company added later is built on its first visit.

export async function generateStaticParams() {
  const rows = await getLatestMomentum();
  return rows.map((row) => ({ id: row.company_id }));
}

export async function generateMetadata({ params }: PageProps<"/companies/[id]">): Promise<Metadata> {
  const { id } = await params;
  const company = await getCompanyDetail(id);
  if (!company) return { title: "Company not found" };
  return pageMetadata(
    `${company.company_name} hiring momentum`,
    `${company.company_name} has ${fmt(company.open_now)} open roles (${company.momentum.toLowerCase()} this week), tracked weekly by HiddenHire.`,
  );
}

export default async function CompanyPage({ params }: PageProps<"/companies/[id]">) {
  const { id } = await params;
  const [company, dates, board] = await Promise.all([
    getCompanyDetail(id),
    getSnapshotDates(),
    getLatestMomentum(),
  ]);
  if (!company) notFound();

  // The trend array lines up with the most recent snapshot dates.
  const trendDates = dates.slice(-company.trend.length);
  const points = company.trend.map((value, index) => ({ date: trendDates[index], value }));
  // Ties go to the most recent week.
  const peak = points.reduce<(typeof points)[number] | null>((best, point) => (!best || point.value >= best.value ? point : best), null);
  const low = points.reduce<(typeof points)[number] | null>((best, point) => (!best || point.value <= best.value ? point : best), null);
  const maxFunction = Math.max(1, ...company.functions.map((row) => row.open_now));
  const website = company.company_website?.split("?")[0];
  const facts = [company.company_stage, company.company_size && `${company.company_size} employees`, shortIndustry(company.industry)]
    .filter(Boolean)
    .join(" · ");

  return (
    <main>
      <PageHeader
        active="/companies"
        eyebrow={
          <Link href="/companies" className="hover:text-white">
            ← All companies
          </Link>
        }
        title={company.company_name}
        description={facts || undefined}
      >
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <MomentumBadge label={company.momentum} />
          <span className="text-sm text-slate-300">
            Ranked #{company.rank} of {board.length} by momentum this week
          </span>
          {website?.startsWith("http") && (
            <a
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-white/25 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              Company website ↗
            </a>
          )}
        </div>
      </PageHeader>

      <section className="mx-auto grid max-w-6xl gap-4 px-4 py-10 sm:grid-cols-3">
        <Stat label="Open roles" value={fmt(company.open_now)} />
        <Stat
          label="Week change"
          value={company.net_change == null ? "—" : signed(company.net_change)}
          tone={company.net_change == null ? undefined : company.net_change > 0 ? "up" : company.net_change < 0 ? "down" : undefined}
          note={MOMENTUM_STYLES[company.momentum].help}
        />
        <Stat
          label="New this week"
          value={company.new_roles == null ? "—" : fmt(company.new_roles)}
          note={company.closed_roles == null ? undefined : `${fmt(company.closed_roles)} closed`}
        />

        <Card className="sm:col-span-2">
          <h2 className="text-sm font-normal text-slate-500">Open roles at each weekly snapshot</h2>
          <div className="mt-4">
            <AreaChart points={points} fromZero />
          </div>
          {peak && low && peak.value !== low.value && (
            <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 text-sm">
              <div>
                <dt className="text-slate-500">Peak</dt>
                <dd className="font-semibold tabular-nums">
                  {fmt(peak.value)} roles <span className="font-normal text-slate-500">on {shortDate(peak.date)}</span>
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Low</dt>
                <dd className="font-semibold tabular-nums">
                  {fmt(low.value)} roles <span className="font-normal text-slate-500">on {shortDate(low.date)}</span>
                </dd>
              </div>
            </dl>
          )}
        </Card>

        <Card>
          <h2 className="text-sm font-normal text-slate-500">Open roles by function</h2>
          <ul className="mt-3 space-y-2.5">
            {company.functions.map((row) => (
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

        <Card className="sm:col-span-3">
          <h2 className="font-semibold">New postings this week</h2>
          {company.new_postings.length === 0 ? (
            <p className="mt-2 text-slate-500">
              {company.new_roles == null
                ? "This company was just added, so there is no earlier week to compare with yet."
                : "No new roles were posted since last week's snapshot."}
            </p>
          ) : (
            <>
              <Postings postings={company.new_postings.slice(0, POSTINGS_SHOWN)} />
              {company.new_postings.length > POSTINGS_SHOWN && (
                // A plain <details> toggle: no JavaScript needed.
                <details className="group">
                  <summary className="mt-2 inline-block cursor-pointer list-none py-1.5 font-semibold text-brand hover:text-blue-500">
                    <span className="group-open:hidden">Show all {company.new_postings.length} new postings</span>
                    <span className="hidden group-open:inline">Show fewer</span>
                  </summary>
                  <Postings postings={company.new_postings.slice(POSTINGS_SHOWN)} />
                </details>
              )}
            </>
          )}
          {trendDates.length > 1 && (
            <p className="mt-4 text-xs text-slate-400">
              Compared with the snapshot closest to a week before {shortDate(trendDates[trendDates.length - 1])}.
            </p>
          )}
        </Card>
      </section>
    </main>
  );
}

const POSTINGS_SHOWN = 10;

function Postings({ postings }: { postings: CompanyDetail["new_postings"] }) {
  return (
    <ul className="mt-3 divide-y divide-slate-100">
      {postings.map((posting, index) => (
        <li key={`${posting.job_url}-${index}`} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2.5">
          {posting.job_url?.startsWith("http") ? (
            <a href={posting.job_url} target="_blank" rel="noopener noreferrer" className="font-medium text-ink hover:text-brand">
              {posting.job_title ?? "Untitled role"} ↗
            </a>
          ) : (
            <span className="font-medium">{posting.job_title ?? "Untitled role"}</span>
          )}
          <span className="text-sm text-slate-500">{posting.location ?? ""}</span>
        </li>
      ))}
    </ul>
  );
}

function Stat({
  label,
  value,
  note,
  tone,
}: {
  label: string;
  value: string;
  note?: ReactNode;
  tone?: "up" | "down";
}) {
  const color = tone === "up" ? "text-up" : tone === "down" ? "text-rose-600" : "text-ink";
  return (
    <Card>
      <h2 className="text-sm font-normal text-slate-500">{label}</h2>
      <p className={`mt-1 text-3xl font-bold tabular-nums ${color}`}>{value}</p>
      {note && <p className="mt-1 text-sm text-slate-500">{note}</p>}
    </Card>
  );
}
