import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHeader } from "@/components/PageHeader";
import { ResultCard } from "@/components/ResultCard";
import { roleLabel, SearchForm } from "@/components/SearchForm";
import { SearchSkeleton } from "@/components/SearchSkeleton";
import { getLatestHeadline } from "@/lib/data";
import { shortDate } from "@/lib/format";
import { joinPhrases } from "@/lib/scoring/explain";
import type { RankedOpportunity } from "@/lib/scoring/types";
import { profileFromParams, runSearch, type SearchParams } from "@/lib/search";

export const metadata: Metadata = {
  title: "Find roles",
  description:
    "Rank open roles at emerging New York startups by your fit and each company's hiring momentum.",
};

// The search page. The header is prebuilt; the form and results depend on
// the address (?role=...&level=...), so they render on each request inside
// a Suspense boundary, with a skeleton shown meanwhile.

export default async function SearchPage({ searchParams }: PageProps<"/search">) {
  const headline = await getLatestHeadline();
  return (
    <main>
      <PageHeader
        active="/search"
        eyebrow={headline ? `Find roles · week of ${shortDate(headline.latest_date)}` : "Find roles"}
        title="Find your hidden opportunities"
        description={
          <>
            Pick your target roles and experience level. HiddenHire ranks every open role at{" "}
            {headline?.companies ?? 43} New York startups by your fit and each company&apos;s hiring
            momentum.
          </>
        }
      />
      <div className="mx-auto max-w-6xl px-4 py-10">
        <Suspense fallback={<SearchSkeleton />}>
          <SearchResults searchParams={searchParams} />
        </Suspense>
      </div>
    </main>
  );
}

async function SearchResults({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { profile, isDefault } = profileFromParams(await searchParams);
  const noRoles = profile.target_roles.length === 0;
  const { comparison, results } = noRoles ? { comparison: null, results: [] } : await runSearch(profile);

  // Results are ranked, so each company's first row is its best match.
  const groups = new Map<string, RankedOpportunity[]>();
  for (const row of results) {
    const rows = groups.get(row.company_id) ?? [];
    rows.push(row);
    groups.set(row.company_id, rows);
  }

  return (
    <div className="space-y-6">
      <SearchForm profile={profile} open={noRoles} />

      {noRoles ? (
        <Notice>Choose at least one target role, then find your matches.</Notice>
      ) : results.length === 0 ? (
        <Notice>
          No current openings for {joinPhrases(profile.target_roles.map(roleLabel))} reached a Candidate
          Fit of 40. Try adding related roles, a different experience level, or a broader location.
        </Notice>
      ) : (
        <section aria-labelledby="results-heading">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              {isDefault && (
                <p className="text-sm font-medium text-brand">
                  A sample search for entry-level business, strategy, and operations analyst roles in New
                  York. Edit it to match your own profile.
                </p>
              )}
              <h2 id="results-heading" className="mt-1 text-2xl font-bold tracking-tight">
                {results.length} matched {results.length === 1 ? "role" : "roles"} at {groups.size}{" "}
                {groups.size === 1 ? "company" : "companies"}
              </h2>
            </div>
            <Link href="/methodology#ranking" className="text-sm font-semibold text-brand hover:text-blue-500">
              How scores work →
            </Link>
          </div>
          <div className="mt-5 space-y-4">
            {[...groups.values()].map((rows) => (
              <ResultCard key={rows[0].company_id} rows={rows} profile={profile} />
            ))}
          </div>
          {comparison && (
            <p className="mt-6 text-sm text-slate-500">
              Openings from the {shortDate(comparison[1])} snapshot. Hiring momentum compares it with{" "}
              {shortDate(comparison[0])}. Opportunity is 60% Candidate Fit and 40% Hiring Momentum.
            </p>
          )}
        </section>
      )}
    </div>
  );
}

function Notice({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-blue-200 bg-blue-50 p-5 text-slate-700">{children}</div>;
}
