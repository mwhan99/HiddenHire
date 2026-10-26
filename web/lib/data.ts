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
