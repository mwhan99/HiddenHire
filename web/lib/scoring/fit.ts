import config from "./config.json";
import { containsTerm, findRoleFamilies, roleMatch } from "./match";
import { npRound, roundHalfEven } from "./rounding";
import type { ScoringJob, SearchProfile, Seniority } from "./types";

// Candidate Fit, mirroring candidate_fit.score_candidate_fit:
// 35% title + 25% seniority + 20% skills + 10% industry + 10% location.

const LEVELS = config.experience_levels as ("entry" | "mid" | "senior")[];
const SENIORITY_SCORES = config.seniority_scores as Record<string, Record<Seniority, number>>;

export const FIT_CUTOFF = 40;

// "Entry level / internship" -> "entry"; anything unknown -> "entry".
export function normalizeExperienceLevel(level: string | null | undefined) {
  const text = String(level || "entry").trim().toLowerCase();
  return LEVELS.find((option) => text.startsWith(option)) ?? "entry";
}

export function seniorityMatch(seniority: Seniority, experienceLevel: string) {
  return SENIORITY_SCORES[normalizeExperienceLevel(experienceLevel)][seniority];
}

// Share of the user's skills found in the description, 0-100, rounded the
// way Python's round() does.
export function skillMatch(description: string | null | undefined, skills: string[]) {
  if (skills.length === 0 || description == null) return 0;
  const found = skills.filter((skill) => containsTerm(description, skill)).length;
  return roundHalfEven((found / skills.length) * 100);
}

export function matchedIndustries(companyIndustry: string | null | undefined, industries: string[]) {
  return industries.filter((industry) => containsTerm(companyIndustry, industry));
}

export function industryMatch(companyIndustry: string | null | undefined, industries: string[]) {
  return matchedIndustries(companyIndustry, industries).length > 0 ? 100 : 0;
}

// Plain substring matching, as in Python (not whole-word).
export function locationMatch(jobLocation: string | null | undefined, preferred: string) {
  if (jobLocation == null) return 0;
  const location = jobLocation.toLowerCase();
  const wanted = preferred.toLowerCase();
  if (wanted === "new york" && ["new york", "nyc", "new york city"].some((term) => location.includes(term))) {
    return 100;
  }
  if (location.includes(wanted)) return 100;
  if (location.includes("remote")) return 75;
  return 0;
}

export type FitRow = {
  job: ScoringJob;
  industry: string | null;
  role_match: number;
  family_match: number;
  title_match: number;
  seniority_match: number;
  skill_match: number;
  industry_match: number;
  location_match: number;
  candidate_fit_score: number;
};

// Score the latest snapshot's jobs and keep the ones Python keeps: in a
// target role family, not two levels away, and a fit of at least 40.
export function scoreCandidateFit(
  latestJobs: ScoringJob[],
  industryByCompany: Map<string, string | null>,
  descriptions: Record<string, string | null>,
  profile: SearchProfile,
): FitRow[] {
  const userFamilies = findRoleFamilies(profile.target_roles);
  const rows: FitRow[] = [];
  for (const job of latestJobs) {
    // role_families was worked out by supabase_sync.py with the same
    // rules (exclusions included), so a shared family means a match.
    const family = job.job_title != null && job.role_families.some((f) => (userFamilies as string[]).includes(f)) ? 75 : 0;
    const role = roleMatch(job.job_title, profile.target_roles);
    const title = role > 0 && family > 0 ? 100 : family;
    const seniority = seniorityMatch(job.seniority, profile.experience_level);
    const industry = industryByCompany.get(job.company_id) ?? null;
    const skill = skillMatch(descriptions[`${job.company_id}|${job.job_id}`], profile.skills);
    const industryScore = industryMatch(industry, profile.industries);
    const location = locationMatch(job.location, profile.location);
    // Same order of additions as the pandas code, so the floats match.
    const fit = npRound(title * 0.35 + seniority * 0.25 + skill * 0.2 + industryScore * 0.1 + location * 0.1, 1);

    if (family > 0 && seniority > 0 && fit >= FIT_CUTOFF) {
      rows.push({
        job,
        industry,
        role_match: role,
        family_match: family,
        title_match: title,
        seniority_match: seniority,
        skill_match: skill,
        industry_match: industryScore,
        location_match: location,
        candidate_fit_score: fit,
      });
    }
  }
  return rows;
}
