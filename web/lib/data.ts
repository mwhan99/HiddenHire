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

export type CompanyMomentum = {
  company_id: string;
  company_name: string;
  open_now: number;
  net_change: number | null;
  new_roles: number | null;
  momentum: "Growing" | "Steady" | "Slowing" | "New to tracking";
  rank: number;
  trend: number[];
};

// The latest Company Momentum leaderboard, best first.
export async function getLatestMomentum(): Promise<CompanyMomentum[]> {
  "use cache";
  cacheLife("hours");

  const latest = await getLatestSnapshotDate();
  if (!latest) return [];
  const { data, error } = await supabase()
    .from("company_momentum")
    .select("company_id, company_name, open_now, net_change, new_roles, momentum, rank, trend")
    .eq("snapshot_date", latest)
    .order("rank");
  if (error) throw new Error(`Could not load Company Momentum: ${error.message}`);
  return data;
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
