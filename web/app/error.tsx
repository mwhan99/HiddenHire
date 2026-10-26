"use client"; // Error pages must run in the browser.

import Link from "next/link";
import { useEffect } from "react";

import { SiteHeader } from "@/components/SiteHeader";

// Shown if a page fails to load, for example if Supabase is briefly
// unreachable during a search. Prebuilt pages keep serving their last good
// copy, so this mostly affects searches. `retry` loads the page again.
export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main>
      <section className="bg-gradient-to-br from-navy to-navy-2 text-white">
        <SiteHeader />
      </section>
      <section className="mx-auto max-w-2xl px-4 py-24 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand">Temporarily unavailable</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">We couldn&apos;t load the hiring data</h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-600">
          The data service didn&apos;t respond. This is usually brief, so please try again in a moment.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={() => retry()}
            className="rounded-lg bg-brand px-5 py-3 font-semibold text-white transition-colors hover:bg-blue-500"
          >
            Try again
          </button>
          <Link
            href="/"
            className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 transition-colors hover:bg-white"
          >
            Back to this week&apos;s briefing
          </Link>
        </div>
      </section>
    </main>
  );
}
