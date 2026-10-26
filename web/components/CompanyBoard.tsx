"use client";

import Link from "next/link";
import { useState } from "react";

import type { CompanyMomentum, MomentumLabel } from "@/lib/data";
import { fmt, shortIndustry, signed } from "@/lib/format";

import { Sparkline } from "./charts";
import { MOMENTUM_LABELS, MomentumBadge } from "./MomentumBadge";

// The Company Momentum leaderboard with a filter by label. It runs in the
// browser so the filter responds instantly; the page around it is still
// prebuilt on the server.

function Change({ value }: { value: number | null }) {
  if (value == null) return <span className="text-slate-400">—</span>;
  const color = value > 0 ? "text-up" : value < 0 ? "text-rose-600" : "text-slate-500";
  return <span className={`font-semibold tabular-nums ${color}`}>{signed(value)}</span>;
}

export function CompanyBoard({ rows }: { rows: CompanyMomentum[] }) {
  const [filter, setFilter] = useState<MomentumLabel | "All">("All");
  const counts = Object.fromEntries(
    MOMENTUM_LABELS.map((label) => [label, rows.filter((row) => row.momentum === label).length]),
  ) as Record<MomentumLabel, number>;
  const shown = filter === "All" ? rows : rows.filter((row) => row.momentum === filter);

  return (
    <div>
      <div role="group" aria-label="Filter by momentum" className="flex flex-wrap gap-2">
        {(["All", ...MOMENTUM_LABELS] as const).map((label) => {
          const count = label === "All" ? rows.length : counts[label];
          if (label !== "All" && count === 0) return null;
          const selected = filter === label;
          return (
            <button
              key={label}
              type="button"
              aria-pressed={selected}
              onClick={() => setFilter(label)}
              className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                selected
                  ? "border-brand bg-brand text-white"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              }`}
            >
              {label} <span className={selected ? "text-blue-100" : "text-slate-400"}>{count}</span>
            </button>
          );
        })}
      </div>

      {/* Table on wider screens */}
      <div className="mt-5 hidden overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_40px_-20px_rgba(11,27,58,0.25)] md:block">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold">#</th>
              <th scope="col" className="px-4 py-3 font-semibold">Company</th>
              <th scope="col" className="px-4 py-3 font-semibold">Momentum</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Open roles</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">Week change</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold">New</th>
              <th scope="col" className="px-4 py-3 font-semibold">Stage</th>
              <th scope="col" className="px-4 py-3 font-semibold">Open roles trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {shown.map((row) => (
              <tr key={row.company_id} className="transition-colors hover:bg-slate-50">
                <td className="px-4 py-3 tabular-nums text-slate-400">{row.rank}</td>
                <td className="px-4 py-3">
                  <Link href={`/companies/${row.company_id}`} className="font-medium text-ink hover:text-brand">
                    {row.company_name}
                  </Link>
                  <div className="text-xs text-slate-500">{shortIndustry(row.industry)}</div>
                </td>
                <td className="px-4 py-3">
                  <MomentumBadge label={row.momentum} />
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{fmt(row.open_now)}</td>
                <td className="px-4 py-3 text-right">
                  <Change value={row.net_change} />
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-600">
                  {row.new_roles == null ? "—" : fmt(row.new_roles)}
                </td>
                <td className="px-4 py-3 text-slate-600">{row.company_stage ?? "—"}</td>
                <td className="px-4 py-3">
                  <Sparkline values={row.trend} width={96} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cards on phones */}
      <ul className="mt-5 space-y-3 md:hidden">
        {shown.map((row) => (
          <li key={row.company_id}>
            <Link
              href={`/companies/${row.company_id}`}
              className="block rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate font-semibold text-ink">{row.company_name}</div>
                  <div className="truncate text-xs text-slate-500">{shortIndustry(row.industry)}</div>
                </div>
                <MomentumBadge label={row.momentum} />
              </div>
              <div className="mt-3 flex items-end justify-between gap-3">
                <div className="text-sm text-slate-600">
                  <span className="font-semibold tabular-nums text-ink">{fmt(row.open_now)}</span> open ·{" "}
                  <Change value={row.net_change} /> this week
                </div>
                <Sparkline values={row.trend} width={80} />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
