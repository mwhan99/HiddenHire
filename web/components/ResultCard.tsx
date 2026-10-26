import Link from "next/link";

import { fmt, shortIndustry } from "@/lib/format";
import { explainOpportunity, momentumBand } from "@/lib/scoring/explain";
import { roundHalfEven } from "@/lib/scoring/rounding";
import type { RankedOpportunity, SearchProfile } from "@/lib/scoring/types";

// One card per company: its best-ranked opening, the reasons, and its
// other matches folded underneath (as on the Streamlit page).

// Whole numbers as Python's f"{x:.0f}" shows them (77.5 -> 78, 76.5 -> 76).
function whole(value: number) {
  return fmt(roundHalfEven(value));
}

const BAND_STYLES = {
  up: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  neutral: "bg-slate-100 text-slate-700 ring-slate-200",
  down: "bg-rose-50 text-rose-700 ring-rose-200",
};
const BAND_ICONS = { up: "▲", neutral: "●", down: "▼" };

export function ResultCard({ rows, profile }: { rows: RankedOpportunity[]; profile: SearchProfile }) {
  const [best, ...others] = rows;
  const band = momentumBand(best.hiring_momentum_score);
  const opportunity = best.hidden_opportunity_score;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_40px_-20px_rgba(11,27,58,0.25)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold leading-snug">{best.job_title ?? "Untitled role"}</h3>
          <Link href={`/companies/${best.company_id}`} className="mt-0.5 inline-block font-medium text-brand hover:text-blue-500">
            {best.company_name}
          </Link>
          <p className="mt-0.5 text-sm text-slate-500">
            {[best.location, shortIndustry(best.industry)].filter(Boolean).join(" · ")}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span
              title="Candidate Fit: how well this role matches your profile (0–100)"
              className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-brand ring-1 ring-inset ring-blue-200"
            >
              Fit {whole(best.candidate_fit_score)}
            </span>
            <span
              title={best.hiring_momentum_score == null ? undefined : `Hiring Momentum ${best.hiring_momentum_score.toFixed(1)} / 100`}
              className={`rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${BAND_STYLES[band.tone]}`}
            >
              <span aria-hidden="true">{BAND_ICONS[band.tone]}</span> {band.label}
            </span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 sm:flex-col sm:items-end sm:gap-0">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Opportunity</span>
          <span className="text-3xl font-bold tabular-nums text-ink">{opportunity == null ? "—" : whole(opportunity)}</span>
        </div>
      </div>

      <div className="mt-4 rounded-xl bg-blue-50/60 p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-brand">Why this opportunity?</div>
        <p className="mt-1 leading-relaxed text-slate-700">{explainOpportunity(best, profile)}</p>
      </div>

      {best.job_url?.startsWith("http") && (
        <a
          href={best.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-block rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-navy-2"
        >
          View job ↗
        </a>
      )}

      {others.length > 0 && (
        <details className="group mt-4 border-t border-slate-100 pt-3">
          <summary className="cursor-pointer list-none py-1.5 text-sm font-semibold text-slate-600 hover:text-ink">
            <span className="inline-block transition-transform group-open:rotate-90">›</span> {others.length} more matching{" "}
            {others.length === 1 ? "role" : "roles"} at {best.company_name}
          </summary>
          <ul className="mt-2 divide-y divide-slate-100">
            {others.map((row) => (
              <li key={row.job_id} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2 text-sm">
                {row.job_url?.startsWith("http") ? (
                  <a href={row.job_url} target="_blank" rel="noopener noreferrer" className="font-medium text-ink hover:text-brand">
                    {row.job_title} ↗
                  </a>
                ) : (
                  <span className="font-medium">{row.job_title}</span>
                )}
                <span className="text-slate-500">
                  Opportunity {row.hidden_opportunity_score == null ? "—" : whole(row.hidden_opportunity_score)}
                  {row.location ? ` · ${row.location}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}
