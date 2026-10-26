import Link from "next/link";

import { Logo } from "./Logo";
import { NAV_LINKS } from "./SiteHeader";

const LINKEDIN_URL = "https://www.linkedin.com/in/meng-wen-han";
const REPO_URL = "https://github.com/mwhan99/HiddenHire";

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-slate-600">
            Built by <span className="font-semibold text-ink">Meng Han</span>, M.S. Management and
            Analytics (Business Analytics), New York University.
          </p>
          <p className="mt-2 text-sm text-slate-500">
            An independent project. Job data comes from public career pages.
          </p>
        </div>
        <nav aria-label="Footer" className="text-sm">
          <div className="font-semibold text-ink">Explore</div>
          <ul className="mt-2 space-y-1 text-slate-600">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="inline-block py-1 hover:text-blue-600">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="text-sm">
          <div className="font-semibold text-ink">Connect</div>
          <ul className="mt-2 space-y-1 text-slate-600">
            <li>
              <a href={LINKEDIN_URL} target="_blank" rel="noopener noreferrer" className="inline-block py-1 hover:text-blue-600">
                LinkedIn ↗
              </a>
            </li>
            <li>
              <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="inline-block py-1 hover:text-blue-600">
                Source on GitHub ↗
              </a>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
