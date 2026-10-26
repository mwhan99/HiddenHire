import Link from "next/link";

import { Logo } from "./Logo";

export const NAV_LINKS = [
  { href: "/search", label: "Find roles" },
  { href: "/companies", label: "Momentum" },
  { href: "/insights", label: "Insights" },
  { href: "/methodology", label: "Methodology" },
];

// The menu bar, drawn for a navy background. `active` is the href of the
// current section, shown in white. On phones only the logo and the main
// button show.
export function SiteHeader({ active }: { active?: string }) {
  return (
    <header className="relative mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
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
    </header>
  );
}
