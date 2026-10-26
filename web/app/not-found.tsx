import type { Metadata } from "next";
import Link from "next/link";

import { SiteHeader } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Page not found",
};

// Shown for any address that does not exist yet, including the pages
// still being built (search, momentum, insights, methodology).
export default function NotFound() {
  return (
    <main>
      <section className="bg-gradient-to-br from-navy to-navy-2 text-white">
        <SiteHeader />
      </section>
      <section className="mx-auto max-w-2xl px-4 py-24 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand">Not here yet</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
          This page is still being built
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-slate-600">
          HiddenHire is moving to a new site, one page at a time. This one isn&apos;t ready yet,
          or the address doesn&apos;t exist.
        </p>
        <Link
          href="/"
          className="mt-8 inline-block rounded-lg bg-brand px-5 py-3 font-semibold text-white transition-colors hover:bg-blue-500"
        >
          Back to this week&apos;s briefing
        </Link>
      </section>
    </main>
  );
}
