import type { Metadata } from "next";

import { CompanyBoard } from "@/components/CompanyBoard";
import { PageHeader } from "@/components/PageHeader";
import { getLatestHeadline, getLatestMomentum } from "@/lib/data";
import { shortDate } from "@/lib/format";
import { pageMetadata } from "@/lib/site";

export const metadata: Metadata = pageMetadata(
  "Company momentum",
  "Every tracked New York startup with open roles, ranked by week-over-week hiring growth relative to company size.",
);

export default async function CompaniesPage() {
  const [headline, rows] = await Promise.all([getLatestHeadline(), getLatestMomentum()]);

  return (
    <main>
      <PageHeader
        active="/companies"
        eyebrow={
          headline
            ? `Company momentum · week of ${shortDate(headline.latest_date)}`
            : "Company momentum"
        }
        title="Who's hiring now"
        description={
          <>
            All {rows.length} tracked startups with open roles, ranked by how fast their open roles
            grew this week relative to their size. A startup with 15 openings that adds 5 outranks
            one with 150 openings that adds 5.
          </>
        }
      />
      <section className="mx-auto max-w-6xl px-4 py-10">
        <CompanyBoard rows={rows} />
        <p className="mt-6 max-w-3xl text-sm leading-relaxed text-slate-500">
          Growth is the week&apos;s net change in open roles divided by the company&apos;s open
          roles a week earlier, counting smaller companies as 10. <b>Growing</b> means at least +5%,{" "}
          <b>Slowing</b> means −5% or lower, and <b>Steady</b> is in between. A company with no
          openings last week is <b>New to tracking</b>. The trend shows open roles at each weekly
          snapshot.
        </p>
      </section>
    </main>
  );
}
