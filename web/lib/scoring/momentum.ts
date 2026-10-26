import type { Family } from "./match";
import { npRound, quantileNearest } from "./rounding";
import type { ScoringJob } from "./types";

// Hiring Momentum, mirroring hiring_momentum.calculate_hiring_momentum:
// 40% new relevant roles + 25% net relevant change + 20% overall growth
// + 15% new postings, each relative to company size and scaled 0-100.

export const TARGET_GAP_DAYS = 7;
export const MIN_GAP_DAYS = 5;
export const MIN_SIZE_FOR_RATES = 10;
export const SCALE_PERCENTILE = 0.9;

const DAY = 24 * 60 * 60 * 1000;

function dayNumber(date: string) {
  return Date.parse(`${date.slice(0, 10)}T00:00:00Z`) / DAY;
}

// [previous, current]: the latest snapshot, and the earlier one closest to
// 7 days before it among those at least 5 days earlier (ties go to the
// later date). Falls back to the one just before while history is short.
export function chooseComparisonDates(snapshotDates: string[]): [string, string] {
  const dates = [...new Set(snapshotDates.map((date) => date.slice(0, 10)))].sort();
  const current = dates[dates.length - 1];
  const earlier = dates.slice(0, -1).filter((date) => dayNumber(current) - dayNumber(date) >= MIN_GAP_DAYS);
  if (earlier.length === 0) return [dates[dates.length - 2], current];
  const target = dayNumber(current) - TARGET_GAP_DAYS;
  const best = [...earlier].sort((a, b) => {
    const gap = Math.abs(dayNumber(a) - target) - Math.abs(dayNumber(b) - target);
    return gap !== 0 ? gap : dayNumber(b) - dayNumber(a);
  })[0];
  return [best, current];
}

function sizeAdjusted(count: number, previousOpen: number) {
  return count / Math.max(previousOpen, MIN_SIZE_FOR_RATES);
}

// Scale one signal to 0-100 across companies: no change is 50, and the
// 90th percentile of non-zero sizes sets how far 100 and 0 are.
export function normalizeSignal(values: number[]): number[] {
  const nonzero = values.filter((value) => value !== 0).map(Math.abs);
  if (nonzero.length === 0) return values.map(() => 50);
  let scale = quantileNearest(nonzero, SCALE_PERCENTILE);
  if (!scale) scale = Math.max(...nonzero);
  return values.map((value) => Math.min(100, Math.max(0, 50 + 50 * (value / scale))));
}

export type CompanyMomentumScore = {
  company_id: string;
  previous_open: number;
  current_open: number;
  new_jobs: number;
  new_relevant: number;
  relevant_change: number;
  new_relevant_component: number;
  relevant_change_component: number;
  job_growth_component: number;
  new_jobs_component: number;
  hiring_momentum_score: number;
};

type Counts = {
  previous_open: number;
  current_open: number;
  new_jobs: number;
  closed_jobs: number;
  new_relevant: number;
  closed_relevant: number;
};

// Momentum for every company in either snapshot. `previousJobs` and
// `currentJobs` must already be limited to active companies.
export function calculateHiringMomentum(
  previousJobs: ScoringJob[],
  currentJobs: ScoringJob[],
  userFamilies: Family[],
): Map<string, CompanyMomentumScore> {
  const families = userFamilies as string[];
  const isRelevant = (job: ScoringJob) => job.job_title != null && job.role_families.some((f) => families.includes(f));
  const counts = new Map<string, Counts>();
  const entry = (companyId: string) => {
    let value = counts.get(companyId);
    if (!value) {
      value = { previous_open: 0, current_open: 0, new_jobs: 0, closed_jobs: 0, new_relevant: 0, closed_relevant: 0 };
      counts.set(companyId, value);
    }
    return value;
  };

  // One row per (company, job ID), as Python's jobs_with_ids does.
  const unique = (jobs: ScoringJob[]) => {
    const byKey = new Map<string, ScoringJob>();
    for (const job of jobs) {
      const id = job.job_id?.trim();
      if (!id) continue;
      const key = `${job.company_id}|${id}`;
      if (!byKey.has(key)) byKey.set(key, job);
    }
    return byKey;
  };
  const previous = unique(previousJobs);
  const current = unique(currentJobs);

  for (const job of previous.values()) entry(job.company_id).previous_open += 1;
  for (const job of current.values()) entry(job.company_id).current_open += 1;
  for (const [key, job] of current) {
    if (previous.has(key)) continue;
    const row = entry(job.company_id);
    row.new_jobs += 1;
    if (isRelevant(job)) row.new_relevant += 1;
  }
  for (const [key, job] of previous) {
    if (current.has(key)) continue;
    const row = entry(job.company_id);
    row.closed_jobs += 1;
    if (isRelevant(job)) row.closed_relevant += 1;
  }

  const ids = [...counts.keys()];
  const rates = ids.map((id) => {
    const row = counts.get(id)!;
    // A company with no openings last time was probably just added, so
    // its signals are held at neutral until it has a baseline.
    if (row.previous_open === 0) return [0, 0, 0, 0];
    return [
      row.new_relevant,
      row.new_relevant - row.closed_relevant,
      row.current_open - row.previous_open,
      row.new_jobs,
    ].map((count) => npRound(sizeAdjusted(count, row.previous_open), 3));
  });
  const components = [0, 1, 2, 3].map((signal) =>
    normalizeSignal(rates.map((rate) => rate[signal])).map((value) => npRound(value, 1)),
  );

  const result = new Map<string, CompanyMomentumScore>();
  ids.forEach((id, index) => {
    const row = counts.get(id)!;
    const [newRelevant, relevantChange, jobGrowth, newJobs] = components.map((signal) => signal[index]);
    result.set(id, {
      company_id: id,
      previous_open: row.previous_open,
      current_open: row.current_open,
      new_jobs: row.new_jobs,
      new_relevant: row.new_relevant,
      relevant_change: row.new_relevant - row.closed_relevant,
      new_relevant_component: newRelevant,
      relevant_change_component: relevantChange,
      job_growth_component: jobGrowth,
      new_jobs_component: newJobs,
      hiring_momentum_score: npRound(newRelevant * 0.4 + relevantChange * 0.25 + jobGrowth * 0.2 + newJobs * 0.15, 1),
    });
  });
  return result;
}
