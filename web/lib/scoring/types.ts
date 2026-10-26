// Shapes shared by the scoring code. Field names follow the Supabase
// columns, so rows from the database can be passed in directly.

export type Seniority = "entry" | "mid" | "senior" | "unknown";

export type ScoringCompany = {
  company_id: string;
  company_name: string;
  industry: string | null;
  active: boolean;
};

export type ScoringJob = {
  snapshot_date: string; // "YYYY-MM-DD"
  company_id: string;
  company_name: string | null;
  job_id: string;
  job_title: string | null;
  location: string | null;
  job_url: string | null;
  role_families: string[]; // added by supabase_sync.py
  seniority: Seniority; // added by supabase_sync.py
};

export type SearchProfile = {
  target_roles: string[];
  skills: string[];
  industries: string[];
  location: string;
  experience_level: string;
};

export type ScoringInput = {
  companies: ScoringCompany[];
  snapshotDates: string[]; // every snapshot date with active companies
  jobs: ScoringJob[]; // at least the latest and comparison snapshots
  descriptions: Record<string, string | null>; // keyed "company_id|job_id"
};

export type RankedOpportunity = {
  company_id: string;
  company_name: string | null;
  job_id: string;
  job_title: string | null;
  location: string | null;
  industry: string | null;
  job_url: string | null;
  candidate_fit_score: number;
  hiring_momentum_score: number | null;
  hidden_opportunity_score: number | null;
  role_match: number;
  family_match: number;
  title_match: number;
  seniority_match: number;
  skill_match: number;
  industry_match: number;
  location_match: number;
};
