import type { Metadata } from "next";

import { getCompanies, getLatestSnapshotDate } from "@/lib/data";

// A temporary page for migration step 6: it proves the site can read
// from Supabase, locally and on Vercel. It goes away once the real
// pages are built.

export const metadata: Metadata = {
  title: "Data check · HiddenHire",
  robots: { index: false },
};

export default async function DataCheckPage() {
  const [companies, latest] = await Promise.all([
    getCompanies(),
    getLatestSnapshotDate(),
  ]);
  const active = companies.filter((company) => company.active);

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold">Supabase data check</h1>
      <p className="mt-2 text-zinc-600">
        {companies.length} companies ({active.length} collected weekly). Latest
        snapshot: {latest ?? "none yet"}.
      </p>
      <ul className="mt-8 divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white">
        {companies.map((company) => (
          <li
            key={company.company_id}
            className="flex items-center justify-between gap-4 px-4 py-3"
          >
            <span className="font-medium">{company.company_name}</span>
            <span className="text-sm text-zinc-500">
              {company.active ? company.ats : `${company.ats} · not collected`}
            </span>
          </li>
        ))}
      </ul>
    </main>
  );
}
