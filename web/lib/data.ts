import { cacheLife } from "next/cache";

import { supabase } from "./supabase";

export type Company = {
  company_id: string;
  company_name: string;
  industry: string | null;
  company_stage: string | null;
  ats: string | null;
  active: boolean;
};

// Every function here is cached for about an hour ("use cache" with the
// "hours" profile). Visitors get a page built ahead of time, and Next.js
// refreshes it in the background, so nobody waits on the database.

export async function getCompanies(): Promise<Company[]> {
  "use cache";
  cacheLife("hours");

  const { data, error } = await supabase()
    .from("companies")
    .select("company_id, company_name, industry, company_stage, ats, active")
    .order("company_name");
  if (error) throw new Error(`Could not load companies: ${error.message}`);
  return data;
}

// The stats-bar numbers for the latest week (market_insights.headline in
// Python). The "previous" fields are null until there are two snapshots.
export type Headline = {
  latest_date: string;
  companies: number;
  open_roles: number;
  previous_date: string | null;
  gap_days: number | null;
  previous_open_roles: number | null;
  new_roles: number | null;
  closed_roles: number | null;
  companies_growing: number | null;
  companies_slowing: number | null;
};

export async function getLatestHeadline(): Promise<Headline | null> {
  "use cache";
  cacheLife("hours");

  const { data, error } = await supabase()
    .from("market_summary")
    .select("headline")
    .order("snapshot_date", { ascending: false })
    .limit(1);
  if (error) throw new Error(`Could not load the latest numbers: ${error.message}`);
  return data[0]?.headline ?? null;
}

export type TrendPoint = { snapshot_date: string; open_roles: number; companies: number };
export type FunctionCount = {
  function: string;
  open_now: number;
  previous_open: number;
  net_change: number;
};

// Open roles at every snapshot and roles by job function, as of the
// latest snapshot (market_insights.open_roles_over_time and
// roles_by_function in Python).
export async function getLatestMarket(): Promise<{
  trend: TrendPoint[];
  functions: FunctionCount[];
} | null> {
  "use cache";
  cacheLife("hours");

  const { data, error } = await supabase()
    .from("market_summary")
    .select("trend, functions")
    .order("snapshot_date", { ascending: false })
    .limit(1);
  if (error) throw new Error(`Could not load Market Insights: ${error.message}`);
  return data[0] ?? null;
}

// One company's week-over-week change (market_insights.company_movers).
export type Mover = {
  company_id: string;
  company: string;
  industry: string | null;
  previous_open: number;
  open_now: number;
  net_change: number;
  change_pct: number;
  new_roles: number;
  closed_roles: number;
  growth_rate: number;
};

export type IndustryCount = {
  industry: string;
  open_now: number;
  previous_open: number;
  net_change: number;
};

export type Briefing = {
  snapshot_date: string;
  headline: Headline;
  growing: Mover[];
  slowing: Mover[];
  functions: FunctionCount[];
  industries: IndustryCount[];
  trend: TrendPoint[];
};

// Everything on the Market Insights page, for the latest snapshot.
export async function getLatestBriefing(): Promise<Briefing | null> {
  "use cache";
  cacheLife("hours");

  const { data, error } = await supabase()
    .from("market_summary")
    .select("snapshot_date, headline, growing, slowing, functions, industries, trend")
    .order("snapshot_date", { ascending: false })
    .limit(1)
    .overrideTypes<Briefing[], { merge: false }>();
  if (error) throw new Error(`Could not load Market Insights: ${error.message}`);
  return data[0] ?? null;
}

export type MomentumLabel ="Growing" | "Steady" | "Slowing" | "New to tracking";

export type CompanyMomentum = {
  company_id: string;
  company_name: string;
  open_now: number;
  net_change: number | null;
  new_roles: number | null;
  closed_roles: number | null;
  growth_rate: number | null;
  momentum: MomentumLabel;
  rank: number;
  trend: number[];
  // From the companies table.
  industry: string | null;
  company_stage: string | null;
  company_size: string | null;
  company_website: string | null;
};

export type CompanyDetail = CompanyMomentum & {
  functions: { function: string; open_now: number }[];
  new_postings: { job_title: string | null; location: string | null; job_url: string | null }[];
};

const MOMENTUM_COLUMNS =
  "company_id, company_name, open_now, net_change, new_roles, closed_roles, growth_rate, momentum, rank, trend, " +
  "companies(industry, company_stage, company_size, company_website)";

type CompanyInfo = Pick<CompanyMomentum, "industry" | "company_stage" | "company_size" | "company_website">;

// Supabase returns the joined company as a nested object; flatten it.
function flatten<T extends { companies: CompanyInfo | null }>(row: T) {
  const { companies, ...rest } = row;
  return {
    ...rest,
    industry: companies?.industry ?? null,
    company_stage: companies?.company_stage ?? null,
    company_size: companies?.company_size ?? null,
    company_website: companies?.company_website ?? null,
  };
}

// The latest Company Momentum leaderboard, best first.
export async function getLatestMomentum(): Promise<CompanyMomentum[]> {
  "use cache";
  cacheLife("hours");

  const latest = await getLatestSnapshotDate();
  if (!latest) return [];
  const { data, error } = await supabase()
    .from("company_momentum")
    .select(MOMENTUM_COLUMNS)
    .eq("snapshot_date", latest)
    .order("rank")
    .overrideTypes<(Omit<CompanyMomentum, keyof CompanyInfo> & { companies: CompanyInfo | null })[], { merge: false }>();
  if (error) throw new Error(`Could not load Company Momentum: ${error.message}`);
  return data.map(flatten);
}

// One company's latest row, with its roles by function and this week's
// new postings. Null when the company is not in the latest snapshot.
export async function getCompanyDetail(companyId: string): Promise<CompanyDetail | null> {
  "use cache";
  cacheLife("hours");

  const latest = await getLatestSnapshotDate();
  if (!latest) return null;
  const { data, error } = await supabase()
    .from("company_momentum")
    .select(`${MOMENTUM_COLUMNS}, functions, new_postings`)
    .eq("snapshot_date", latest)
    .eq("company_id", companyId)
    .limit(1)
    .overrideTypes<(Omit<CompanyDetail, keyof CompanyInfo> & { companies: CompanyInfo | null })[], { merge: false }>();
  if (error) throw new Error(`Could not load ${companyId}: ${error.message}`);
  return data[0] ? flatten(data[0]) : null;
}

// Every snapshot date, oldest first. Company trend arrays line up with it.
export async function getSnapshotDates(): Promise<string[]> {
  "use cache";
  cacheLife("hours");

  const market = await getLatestMarket();
  return (market?.trend ?? []).map((point) => point.snapshot_date.slice(0, 10));
}

export async function getLatestSnapshotDate(): Promise<string | null> {
  "use cache";
  cacheLife("hours");

  const { data, error } = await supabase()
    .from("market_summary")
    .select("snapshot_date")
    .order("snapshot_date", { ascending: false })
    .limit(1);
  if (error) throw new Error(`Could not load the latest snapshot: ${error.message}`);
  return data[0]?.snapshot_date ?? null;
}
