import Link from "next/link";

import { Logo } from "./Logo";

export const NAV_LINKS = [
  { href: "/search", label: "Find roles" },
  { href: "/companies", label: "Momentum" },
  { href: "/insights", label: "Insights" },
  { href: "/methodology", label: "Methodology" },
];

// The menu bar, drawn for a navy background. `active` is the href of the
// current section, shown in white. On phones the links move to a second
// row under the logo, which scrolls sideways if it doesn't fit.
export function SiteHeader({ active }: { active?: string }) {
  return (
    <header className="relative mx-auto max-w-6xl px-4 pt-5 md:pb-5">
      <div className="flex items-center justify-between">
        <Logo dark />
        <nav aria-label="Main" className="hidden items-center gap-8 text-[15px] md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={link.href === active ? "page" : undefined}
              className={
                link.href === active
                  ? "font-medium text-white"
                  : "text-slate-300 transition-colors hover:text-white"
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <Link
          href="/search"
          className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-blue-50"
        >
          Find my matches
        </Link>
      </div>
      <nav aria-label="Main" className="-mx-4 mt-4 flex gap-2 overflow-x-auto px-4 pb-3 md:hidden">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            aria-current={link.href === active ? "page" : undefined}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm transition-colors ${
              link.href === active
                ? "bg-white/15 font-medium text-white"
                : "text-slate-300 hover:bg-white/10 hover:text-white"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
