import { cacheLife } from "next/cache";

import { getSnapshotDates } from "./data";
import { findRoleFamilies, SUPPORTED_ROLES } from "./scoring/match";
import { chooseComparisonDates } from "./scoring/momentum";
import { rankHiddenOpportunities } from "./scoring/rank";
import type { ScoringCompany, ScoringInput, ScoringJob, SearchProfile } from "./scoring/types";
import { supabase } from "./supabase";

// Loads exactly what one search needs from Supabase and ranks it with the
// TypeScript scoring (web/lib/scoring, tested against the Python code).
//
// Momentum needs every job in the two compared snapshots, but only a few
// short columns. Fit needs full details only for jobs in the searched role
// families, plus their descriptions. Keeping the requests that small
// matters because on Vercel a search can't count on a warm cache.

export const DEFAULT_PROFILE: SearchProfile = {
  target_roles: ["business analyst", "strategy analyst", "operations analyst"],
  skills: ["SQL", "Excel", "Tableau", "Python"],
  industries: ["fintech", "AI", "enterprise software"],
  location: "New York",
  experience_level: "entry",
};

const PAGE = 1000; // Supabase returns at most 1,000 rows per request

async function allRows<T>(query: (from: number, to: number) => PromiseLike<{ data: T[] | null; error: { message: string } | null }>) {
  const rows: T[] = [];
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await query(from, from + PAGE - 1);
    if (error) throw new Error(`Could not load search data: ${error.message}`);
    rows.push(...(data ?? []));
    if (!data || data.length < PAGE) return rows;
  }
}

async function getCompaniesForScoring(): Promise<ScoringCompany[]> {
  "use cache";
  cacheLife("hours");
  const { data, error } = await supabase().from("companies").select("company_id, company_name, industry, active");
  if (error) throw new Error(`Could not load companies: ${error.message}`);
  return data;
}

// Every job in one snapshot, with only the columns momentum needs.
async function getSnapshotSkeleton(date: string): Promise<ScoringJob[]> {
  "use cache";
  cacheLife("hours");
  const rows = await allRows<{ company_id: string; job_id: string; job_title: string | null; role_families: string[] }>((from, to) =>
    supabase()
      .from("job_snapshots")
      .select("company_id, job_id, job_title, role_families")
      .eq("snapshot_date", date)
      .order("company_id")
      .order("job_id")
      .range(from, to),
  );
  return rows.map((row) => ({
    ...row,
    snapshot_date: date,
    company_name: null,
    location: null,
    job_url: null,
    seniority: "unknown",
  }));
}

// Full details and descriptions for the latest jobs in the given families.
async function getCandidateJobs(date: string, families: string[]) {
  "use cache";
  cacheLife("hours");
  if (families.length === 0) return { jobs: [] as ScoringJob[], descriptions: {} as Record<string, string | null> };
  const jobs = await allRows<ScoringJob>((from, to) =>
    supabase()
      .from("job_snapshots")
      .select("snapshot_date, company_id, company_name, job_id, job_title, location, job_url, role_families, seniority")
      .eq("snapshot_date", date)
      .overlaps("role_families", families)
      .order("company_id")
      .order("job_id")
      .range(from, to),
  );

  const descriptions: Record<string, string | null> = {};
  const ids = [...new Set(jobs.map((job) => job.job_id))];
  const chunks = Array.from({ length: Math.ceil(ids.length / 100) }, (_, i) => ids.slice(i * 100, i * 100 + 100));
  const results = await Promise.all(
    chunks.map((chunk) => supabase().from("job_descriptions").select("company_id, job_id, description").in("job_id", chunk)),
  );
  for (const { data, error } of results) {
    if (error) throw new Error(`Could not load job descriptions: ${error.message}`);
    for (const row of data ?? []) descriptions[`${row.company_id}|${row.job_id}`] = row.description;
  }
  return { jobs, descriptions };
}

export type SearchResults = Awaited<ReturnType<typeof runSearch>>;

export async function runSearch(profile: SearchProfile) {
  const snapshotDates = await getSnapshotDates();
  if (snapshotDates.length === 0) return { comparison: null, latest: null, results: [] };
  const comparison = snapshotDates.length >= 2 ? chooseComparisonDates(snapshotDates) : null;
  const latest = comparison ? comparison[1] : snapshotDates[0];
  const families = findRoleFamilies(profile.target_roles);

  const [companies, latestSkeleton, previousSkeleton, candidates] = await Promise.all([
    getCompaniesForScoring(),
    getSnapshotSkeleton(latest),
    comparison ? getSnapshotSkeleton(comparison[0]) : Promise.resolve([]),
    getCandidateJobs(latest, families),
  ]);

  // Candidate rows carry full details; the rest of the latest snapshot only
  // feeds momentum.
  const detailed = new Set(candidates.jobs.map((job) => `${job.company_id}|${job.job_id}`));
  const input: ScoringInput = {
    companies,
    snapshotDates,
    jobs: [
      ...previousSkeleton,
      ...candidates.jobs,
      ...latestSkeleton.filter((job) => !detailed.has(`${job.company_id}|${job.job_id}`)),
    ],
    descriptions: candidates.descriptions,
  };
  const { results } = rankHiddenOpportunities(input, profile);
  return { comparison, latest, results };
}

// ---- Reading a search from the address --------------------------------

function list(value: string | string[] | undefined) {
  return (Array.isArray(value) ? value : value ? [value] : []).filter(Boolean);
}

function csv(value: string | undefined) {
  return (value ?? "").split(",").map((item) => item.trim()).filter(Boolean);
}

export type SearchParams = Record<string, string | string[] | undefined>;

// /search with no values runs the default analyst search, so the page is
// never empty. Unknown role names are ignored.
export function profileFromParams(params: SearchParams): { profile: SearchProfile; isDefault: boolean } {
  const searched = ["role", "level", "skills", "industries", "location"].some((key) => key in params);
  if (!searched) return { profile: DEFAULT_PROFILE, isDefault: true };
  const roles = list(params.role)
    .map((role) => role.toLowerCase().trim())
    .filter((role, index, all) => SUPPORTED_ROLES.includes(role) && all.indexOf(role) === index);
  const level = list(params.level)[0] ?? "entry";
  return {
    profile: {
      target_roles: roles,
      experience_level: ["entry", "mid", "senior"].includes(level) ? level : "entry",
      skills: csv(list(params.skills)[0]),
      industries: csv(list(params.industries)[0]),
      location: (list(params.location)[0] ?? "").trim(),
    },
    isDefault: false,
  };
}
