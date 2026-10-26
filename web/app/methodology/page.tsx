import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Card } from "@/components/Card";
import { PageHeader } from "@/components/PageHeader";
import { getCoverage } from "@/lib/data";
import { fmt, longDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How HiddenHire collects weekly job snapshots, scores Candidate Fit and Hiring Momentum, " +
    "ranks openings, and what its limits are.",
};

// Every number on this page must match the Python code (candidate_fit.py,
// hiring_momentum.py, pipeline.py, market_insights.py), the README's
// Scoring section, and app.py's Methodology tab. Change them together.

const REPO_URL = "https://github.com/mwhan99/HiddenHire";

const SECTIONS = [
  { id: "how-it-works", label: "How it works" },
  { id: "coverage", label: "Coverage" },
  { id: "candidate-fit", label: "Candidate Fit" },
  { id: "hiring-momentum", label: "Hiring Momentum" },
  { id: "ranking", label: "Ranking" },
  { id: "company-momentum", label: "Company Momentum" },
  { id: "data-quality", label: "Data quality fixes" },
  { id: "limitations", label: "Limitations" },
  { id: "how-its-built", label: "How it's built" },
];

const STEPS = [
  { name: "Collect", text: "Every Monday, GitHub Actions pulls each company's public job board from Ashby, Greenhouse, or Lever." },
  { name: "Snapshot", text: "That day's openings are added to a dated history, so postings can be compared week over week." },
  { name: "Score", text: "Each opening gets a Candidate Fit score against your profile; each company gets a Hiring Momentum score." },
  { name: "Rank", text: "Openings are ranked 60% fit, 40% momentum, with a plain-language reason and a link to the posting." },
];

type Weight = { name: string; weight: number; text: string };

const FIT_WEIGHTS: Weight[] = [
  { name: "Title", weight: 35, text: "100 when the title contains one of your target roles as a whole phrase, 75 for another title in the same role family." },
  { name: "Seniority", weight: 25, text: "The title is classified as entry, mid, senior, or unknown and compared with your experience level (table below)." },
  { name: "Skills", weight: 20, text: "The share of your skills found in the posting. Three of four skills scores 75; a posting with no description scores 0." },
  { name: "Industry", weight: 10, text: "Full credit when the company is in any of your preferred industries." },
  { name: "Location", weight: 10, text: "Full credit for your location (“New York” also matches “NYC”), 75 for remote, otherwise 0." },
];

const MOMENTUM_WEIGHTS: Weight[] = [
  { name: "New relevant roles", weight: 40, text: "Roles opened this week in your target role families." },
  { name: "Net relevant change", weight: 25, text: "New minus closed roles in those families." },
  { name: "Overall growth", weight: 20, text: "Change in all open roles at the company." },
  { name: "New postings", weight: 15, text: "All roles opened this week." },
];

const SENIORITY: { level: string; scores: number[] }[] = [
  { level: "Entry", scores: [100, 40, 0, 50] },
  { level: "Mid", scores: [50, 100, 40, 50] },
  { level: "Senior", scores: [0, 50, 100, 50] },
];

const DATA_FIXES = [
  { name: "Missing descriptions", text: "The Greenhouse collector stored no job descriptions, so more than a quarter of all postings scored 0 on skills. It now requests and cleans the full text, and Lever postings include their requirement bullets." },
  { name: "One-day momentum window", text: "Momentum compared the two most recent snapshots, which were one day apart when a manual run followed a scheduled one. It now uses the snapshot closest to seven days earlier." },
  { name: "Substring matching", text: "“Excel” matched “excellent” (519 postings contained “excel”; 53 mentioned the skill), “AI” matched “supply chain”, and “intern” matched “international”. All matching is now whole-word." },
  { name: "Hard-coded relevance", text: "Momentum always counted analyst roles, whatever you searched for. It now uses your target roles." },
  { name: "Size bias", text: "Raw job counts made the largest employers look hottest. Every signal is now relative to company size." },
];

const LIMITATIONS = [
  { name: "Coverage", text: "Results only include the companies on the list. A strong opening elsewhere won't appear." },
  { name: "Short history", text: "Snapshots start in September 2026. With a few weeks of data, one posting at a small company can move its score noticeably, and whether high momentum predicts continued hiring hasn't been tested yet." },
  { name: "Rule-based matching", text: "Skills and roles match by keyword, so synonyms (“BI” vs. “business intelligence”), plurals, and roles outside the built-in families are missed." },
  { name: "Seniority from titles", text: "Experience level comes from job titles only; requirements in the description, such as “3+ years”, aren't read." },
  { name: "Simple location matching", text: "Locations match as text, and every remote posting gets partial credit regardless of region." },
];

const ARCHITECTURE = [
  { name: "Public job boards", detail: "Ashby, Greenhouse, and Lever APIs" },
  { name: "Python collectors", detail: "GitHub Actions, every Monday at 8 AM New York time" },
  { name: "Supabase", detail: "Postgres with read-only access for the site, kept awake daily" },
  { name: "Next.js on Vercel", detail: "Pages prebuilt and refreshed about hourly" },
];

export default async function MethodologyPage() {
  const data = await getCoverage();
  const coverage = data?.coverage;
  const trend = data?.trend ?? [];
  const ats = coverage
    ? Object.entries(coverage.by_ats).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <main>
      <PageHeader
        active="/methodology"
        eyebrow="Methodology"
        title="How HiddenHire works"
        description="Every score is rule-based and explainable: no language model is involved, and every explanation is built only from signals the scores support."
      />

      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-[200px_1fr]">
        {/* Table of contents, sticky on wide screens */}
        <nav aria-label="On this page" className="hidden lg:block">
          <div className="sticky top-6">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">On this page</div>
            <ul className="mt-3 space-y-2 text-sm">
              {SECTIONS.map((section) => (
                <li key={section.id}>
                  <a href={`#${section.id}`} className="text-slate-600 hover:text-brand">
                    {section.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        <div className="min-w-0 space-y-14">
          <Section id="how-it-works" title="How it works">
            <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((step, index) => (
                <li key={step.name}>
                  <Card className="h-full">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-brand">
                      {index + 1}
                    </span>
                    <h3 className="mt-3 font-semibold">{step.name}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{step.text}</p>
                  </Card>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="coverage" title="Coverage">
            <Prose>
              {coverage ? fmt(coverage.curated) : "Fifty"} venture-backed New York startups were
              hand-picked in September 2026 from StartupsGallery, TopStartups, and Y Combinator&apos;s
              directory, mostly Series A–B with 11–500 employees, across AI, fintech, health tech, and
              enterprise software.
            </Prose>
            {coverage && (
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <Card>
                  <div className="text-sm text-slate-500">Collected every week</div>
                  <div className="mt-1 text-3xl font-bold tabular-nums">
                    {coverage.active}
                    <span className="text-lg font-medium text-slate-400"> / {coverage.curated}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    The rest use job boards without a collector yet (Gem, Comeet, Dover) or are marked inactive.
                  </div>
                </Card>
                <Card>
                  <div className="text-sm text-slate-500">By job board</div>
                  <ul className="mt-2 space-y-1.5 text-sm">
                    {ats.map(([name, count]) => (
                      <li key={name} className="flex justify-between">
                        <span>{name}</span>
                        <span className="tabular-nums text-slate-500">{count}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
                <Card>
                  <div className="text-sm text-slate-500">Snapshot history</div>
                  <div className="mt-1 text-3xl font-bold tabular-nums">{trend.length}</div>
                  <div className="mt-1 text-sm text-slate-500">
                    {trend.length > 0 && <>snapshots since {longDate(trend[0].snapshot_date)}</>}
                  </div>
                </Card>
              </div>
            )}
          </Section>

          <Section id="candidate-fit" title="Candidate Fit">
            <Prose>
              How well one opening matches your profile, from 0 to 100. You pick target roles from 40
              titles in 8 role families (business analytics, strategy, operations, finance, marketing and
              growth, product, software engineering, data science and ML), and similar titles in the same
              family count too. Unrelated &ldquo;operations&rdquo; titles, such as people, legal, or
              clinical operations, never match.
            </Prose>
            <WeightTable weights={FIT_WEIGHTS} />
            <Card className="mt-4">
              <h3 className="font-semibold">Seniority score</h3>
              <p className="mt-1 text-sm text-slate-500">
                Rows are your experience level; columns are the level read from the job title (&ldquo;Unclear&rdquo; when no level word appears). The first
                match wins, checked in the order senior → entry → mid.
              </p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-xs uppercase tracking-wider text-slate-500">
                    <tr className="border-b border-slate-200">
                      <th scope="col" className="py-2 pr-2 text-left font-semibold sm:pr-4">You are</th>
                      {["Entry", "Mid", "Senior", "Unclear"].map((label) => (
                        <th key={label} scope="col" className="px-2 py-2 text-right font-semibold sm:px-3">{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {SENIORITY.map((row) => (
                      <tr key={row.level}>
                        <th scope="row" className="py-2 pr-4 text-left font-medium">{row.level}</th>
                        {row.scores.map((score, index) => (
                          <td key={index} className={`px-2 py-2 text-right sm:px-3 tabular-nums ${score === 100 ? "font-semibold text-brand" : score === 0 ? "text-slate-400" : ""}`}>
                            {score}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            <Prose className="mt-4">
              Only openings in your role families with a fit of <b>at least 40</b> are shown, and titles
              two levels away from your experience level (a Director role in an entry-level search) are
              left out. Skills, roles, industries, and seniority words match as whole words, so
              &ldquo;Excel&rdquo; doesn&apos;t match &ldquo;excellent&rdquo;.
            </Prose>
          </Section>

          <Section id="hiring-momentum" title="Hiring Momentum">
            <Prose>
              How fast a company is adding roles, from 0 to 100. It compares the latest snapshot with the
              one closest to 7 days earlier (at least 5 days earlier, so an extra manual run doesn&apos;t
              shrink the window). Because two of the signals count roles in <i>your</i> target families,
              momentum changes with your search.
            </Prose>
            <WeightTable weights={MOMENTUM_WEIGHTS} />
            <Prose className="mt-4">
              Every signal is divided by the company&apos;s open roles a week earlier, counting smaller
              companies as 10, so 5 new roles at a startup with 15 openings outweigh 5 at one with 150.
              Each signal is then scaled against the 90th percentile across companies, so one extreme
              company doesn&apos;t flatten everyone else: no change scores 50, growth moves toward 100,
              and shrinking toward 0. A company with no openings a week earlier has no baseline yet and
              scores a neutral 50.
            </Prose>
          </Section>

          <Section id="ranking" title="Ranking">
            <Card className="border-blue-200 bg-blue-50/50">
              <p className="text-lg font-semibold">Opportunity = 60% Candidate Fit + 40% Hiring Momentum</p>
              <p className="mt-2 text-slate-600">
                Results are sorted by Opportunity, then fit, and shown one card per company with its other
                matches underneath. A momentum of 60 or more reads <b>Hiring fast</b>, 45 to 60{" "}
                <b>Steady hiring</b>, and below 45 <b>Quieter hiring</b>.
              </p>
            </Card>
          </Section>

          <Section id="company-momentum" title="Company Momentum">
            <Prose>
              The Company Momentum page ranks companies by their net change in open roles relative to
              size, using the same window and size adjustment as Hiring Momentum, but counting all roles,
              so it&apos;s the same for every visitor. A company is <b>Growing</b> at +5% or more,{" "}
              <b>Slowing</b> at −5% or less, and <b>Steady</b> in between; one with no openings the week
              before is <b>New to tracking</b>. Job functions in Market Insights are assigned from titles
              by keyword, so a small share of postings land in &ldquo;Other&rdquo;.
            </Prose>
          </Section>

          <Section id="data-quality" title="Data quality fixes">
            <Prose>Problems found in the data and scoring, and how they were fixed. Each fix has tests in the repository.</Prose>
            <ItemList items={DATA_FIXES} />
          </Section>

          <Section id="limitations" title="Limitations">
            <ItemList items={LIMITATIONS} />
          </Section>

          <Section id="how-its-built" title="How it's built">
            <ol className="grid gap-3 lg:grid-cols-4">
              {ARCHITECTURE.map((stage, index) => (
                <li key={stage.name} className="relative">
                  <Card className="h-full">
                    <div className="text-xs font-semibold uppercase tracking-wider text-brand">Step {index + 1}</div>
                    <div className="mt-1 font-semibold">{stage.name}</div>
                    <div className="mt-1 text-sm text-slate-600">{stage.detail}</div>
                  </Card>
                  {index < ARCHITECTURE.length - 1 && (
                    <span aria-hidden="true" className="absolute -bottom-3 left-1/2 z-10 -translate-x-1/2 text-slate-400 lg:-right-3 lg:bottom-auto lg:left-auto lg:top-1/2 lg:-translate-y-1/2 lg:translate-x-1/2">
                      <span className="lg:hidden">↓</span>
                      <span className="hidden lg:inline">→</span>
                    </span>
                  )}
                </li>
              ))}
            </ol>
            <Prose className="mt-6">
              Scoring is written in Python with pandas and covered by pytest. The collectors still save an
              Excel workbook as a backup while the site moves from Streamlit to Next.js, TypeScript, and
              Tailwind.
            </Prose>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-block rounded-lg bg-brand px-5 py-3 font-semibold text-white transition-colors hover:bg-blue-500"
            >
              View the source on GitHub ↗
            </a>
          </Section>
        </div>
      </div>
    </main>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-6">
      <h2 className="mb-4 text-2xl font-bold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

function Prose({ className = "", children }: { className?: string; children: ReactNode }) {
  return <p className={`max-w-3xl leading-relaxed text-slate-700 ${className}`}>{children}</p>;
}

// A stacked bar showing the weights, then one row per part.
function WeightTable({ weights }: { weights: Weight[] }) {
  const shades = ["bg-blue-700", "bg-blue-600", "bg-blue-500", "bg-blue-400", "bg-blue-300"];
  return (
    <Card className="mt-6">
      <div className="flex h-3 overflow-hidden rounded-full" role="img" aria-label={weights.map((w) => `${w.name} ${w.weight}%`).join(", ")}>
        {weights.map((w, index) => (
          <span key={w.name} className={`${shades[index]} h-full`} style={{ width: `${w.weight}%` }} />
        ))}
      </div>
      <ul className="mt-5 divide-y divide-slate-100">
        {weights.map((w, index) => (
          <li key={w.name} className="grid gap-1 py-3 sm:grid-cols-[180px_1fr] sm:gap-4">
            <div className="flex items-center gap-2 font-medium">
              <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-full ${shades[index]}`} />
              {w.name}
              <span className="ml-auto rounded bg-blue-50 px-1.5 py-0.5 text-xs font-semibold tabular-nums text-brand sm:ml-1">
                {w.weight}%
              </span>
            </div>
            <p className="text-sm leading-relaxed text-slate-600">{w.text}</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function ItemList({ items }: { items: { name: string; text: string }[] }) {
  return (
    <ul className="mt-4 grid gap-4 sm:grid-cols-2">
      {items.map((item) => (
        <li key={item.name}>
          <Card className="h-full">
            <h3 className="font-semibold">{item.name}</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{item.text}</p>
          </Card>
        </li>
      ))}
    </ul>
  );
}
