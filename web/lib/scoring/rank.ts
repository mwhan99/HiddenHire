import { scoreCandidateFit } from "./fit";
import { findRoleFamilies } from "./match";
import { calculateHiringMomentum, chooseComparisonDates, type CompanyMomentumScore } from "./momentum";
import { npRound } from "./rounding";
import type { RankedOpportunity, ScoringInput, SearchProfile } from "./types";

// Hidden Opportunity ranking, mirroring pipeline.rank_hidden_opportunities:
// 60% Candidate Fit + 40% Hiring Momentum, best first.

export type RankingResult = {
  comparison: [string, string] | null;
  results: RankedOpportunity[];
  momentum: Map<string, CompanyMomentumScore>;
};

// Python compares strings by code point; so does `<` on these strings.
function compareText(a: string | null, b: string | null) {
  const left = a ?? "";
  const right = b ?? "";
  return left < right ? -1 : left > right ? 1 : 0;
}

// Descending, with missing values last (pandas' default).
function compareDesc(a: number | null, b: number | null) {
  if (a === b) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  return b - a;
}

export function rankHiddenOpportunities(input: ScoringInput, profile: SearchProfile): RankingResult {
  const active = new Set(input.companies.filter((company) => company.active).map((company) => company.company_id));
  const industryByCompany = new Map(input.companies.map((company) => [company.company_id, company.industry]));
  const jobs = input.jobs.filter((job) => active.has(job.company_id));
  if (input.snapshotDates.length === 0) return { comparison: null, results: [], momentum: new Map() };

  const comparison = input.snapshotDates.length >= 2 ? chooseComparisonDates(input.snapshotDates) : null;
  const latest = comparison ? comparison[1] : input.snapshotDates[0].slice(0, 10);
  const latestJobs = jobs.filter((job) => job.snapshot_date.slice(0, 10) === latest);

  const fit = scoreCandidateFit(latestJobs, industryByCompany, input.descriptions, profile);
  const momentum = comparison
    ? calculateHiringMomentum(
        jobs.filter((job) => job.snapshot_date.slice(0, 10) === comparison[0]),
        latestJobs,
        findRoleFamilies(profile.target_roles),
      )
    : new Map<string, CompanyMomentumScore>();

  const results: RankedOpportunity[] = fit.map((row) => {
    const score = momentum.get(row.job.company_id)?.hiring_momentum_score ?? null;
    return {
      company_id: row.job.company_id,
      company_name: row.job.company_name,
      job_id: row.job.job_id,
      job_title: row.job.job_title,
      location: row.job.location,
      industry: row.industry,
      job_url: row.job.job_url,
      candidate_fit_score: row.candidate_fit_score,
      hiring_momentum_score: score,
      hidden_opportunity_score: score == null ? null : npRound(0.6 * row.candidate_fit_score + 0.4 * score, 1),
      role_match: row.role_match,
      family_match: row.family_match,
      title_match: row.title_match,
      seniority_match: row.seniority_match,
      skill_match: row.skill_match,
      industry_match: row.industry_match,
      location_match: row.location_match,
    };
  });

  // Opportunity, then fit (both high to low), then company and title (A-Z).
  results.sort(
    (a, b) =>
      compareDesc(a.hidden_opportunity_score, b.hidden_opportunity_score) ||
      compareDesc(a.candidate_fit_score, b.candidate_fit_score) ||
      compareText(a.company_name, b.company_name) ||
      compareText(a.job_title, b.job_title),
  );
  return { comparison, results, momentum };
}
