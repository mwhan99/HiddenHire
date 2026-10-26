import { readFileSync } from "node:fs";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";

import { describe, expect, test } from "vitest";

import { explainOpportunity, joinPhrases } from "./explain";
import { locationMatch, normalizeExperienceLevel, skillMatch } from "./fit";
import { containsTerm, findRoleFamilies, roleMatch } from "./match";
import { chooseComparisonDates, normalizeSignal } from "./momentum";
import { rankHiddenOpportunities } from "./rank";
import { npRound, quantileNearest, roundHalfEven } from "./rounding";
import type { RankedOpportunity, ScoringCompany, ScoringJob, SearchProfile } from "./types";

// The golden file holds Python's results for fixed searches
// (scripts/export_golden.py). The TypeScript must reproduce them exactly.

type ExpectedRow = {
  company_name: string;
  job_title: string;
  location: string | null;
  industry: string | null;
  job_url: string | null;
  candidate_fit_score: number;
  hiring_momentum_score: number | null;
  hidden_opportunity_score: number | null;
  family_match: number;
  skill_match: number;
  industry_match: number;
  location_match: number;
  explanation: string;
};

type Golden = {
  snapshot_dates: string[];
  comparison: { previous: string; current: string };
  companies: ScoringCompany[];
  jobs: ScoringJob[];
  descriptions: Record<string, string | null>;
  cases: {
    name: string;
    profile: SearchProfile;
    expected: ExpectedRow[];
    momentum: Record<string, Record<string, number>>;
  }[];
};

const golden: Golden = JSON.parse(
  gunzipSync(readFileSync(join(__dirname, "__fixtures__", "golden.json.gz"))).toString("utf8"),
);

// The workbook keeps a few titles with a trailing space; supabase_sync.py
// trims them, so the website (and these inputs) never see it. Compare the
// trimmed titles.
for (const testCase of golden.cases) {
  for (const row of testCase.expected) row.job_title = row.job_title?.trim();
}

const input = {
  companies: golden.companies,
  snapshotDates: golden.snapshot_dates,
  jobs: golden.jobs,
  descriptions: golden.descriptions,
};

describe("rounding matches Python", () => {
  test("round() sends .5 to the even neighbour", () => {
    expect([12.5, 13.5, 2.5, -2.5, 0.4, 0.6].map(roundHalfEven)).toEqual([12, 14, 2, -2, 0, 1]);
  });
  test("pandas Series.round multiplies first", () => {
    expect([0.25, 0.35, 92.45, 26.25].map((x) => npRound(x, 1))).toEqual([0.2, 0.4, 92.4, 26.2]);
    expect([0.0625, 0.1665].map((x) => npRound(x, 3))).toEqual([0.062, 0.166]);
  });
  test("quantile(0.9, nearest) rounds the position to even", () => {
    const range = (n: number) => Array.from({ length: n }, (_, i) => i + 1);
    expect([2, 3, 6, 16, 26].map((n) => quantileNearest(range(n), 0.9))).toEqual([2, 3, 5, 15, 23]);
  });
});

describe("matching rules (same cases as tests/test_candidate_fit.py)", () => {
  test("whole-word matching", () => {
    expect(containsTerm("Excellent communication", "excel")).toBe(false);
    expect(containsTerm("Advanced Excel and SQL", "excel")).toBe(true);
    expect(containsTerm("C++, FP&A experience", "c++")).toBe(true);
    expect(containsTerm("C++, FP&A experience", "fp&a")).toBe(true);
    expect(containsTerm("Supply chain", "ai")).toBe(false);
    expect(containsTerm("International Sales", "intern")).toBe(false);
    expect(containsTerm(null, "sql")).toBe(false);
    expect(containsTerm("sql", "  ")).toBe(false);
  });
  test("skills are a share of the list, rounded like Python", () => {
    expect(skillMatch("We use SQL and Excel", ["SQL", "Excel", "Tableau", "Python"])).toBe(50);
    expect(skillMatch("SQL", ["SQL", "a", "b", "c", "d", "e", "f", "g"])).toBe(12); // 12.5 -> 12
    expect(skillMatch(null, ["SQL"])).toBe(0);
    expect(skillMatch("SQL", [])).toBe(0);
  });
  test("excluded titles get no role credit", () => {
    expect(roleMatch("People Operations Analyst", ["operations analyst"])).toBe(0);
    expect(roleMatch("Senior Operations Analyst", ["operations analyst"])).toBe(100);
  });
  test("experience labels and locations", () => {
    expect(normalizeExperienceLevel("Entry level / internship")).toBe("entry");
    expect(normalizeExperienceLevel("Mid level")).toBe("mid");
    expect(normalizeExperienceLevel("unknown")).toBe("entry");
    expect(locationMatch("NYC (Hybrid)", "New York")).toBe(100);
    expect(locationMatch("Remote - US", "New York")).toBe(75);
    expect(locationMatch(null, "New York")).toBe(0);
  });
  test("role families and phrases", () => {
    expect(findRoleFamilies(["Business Analyst", "product operations"])).toEqual(["business_analytics", "operations", "product"]);
    expect(joinPhrases(["a", "b", "c"])).toBe("a, b, and c");
  });
  test("a flat signal scores 50", () => {
    expect(normalizeSignal([0, 0, 0])).toEqual([50, 50, 50]);
  });
});

test("picks the same comparison snapshots as Python", () => {
  expect(chooseComparisonDates(golden.snapshot_dates)).toEqual([golden.comparison.previous, golden.comparison.current]);
});

const key = (row: { hidden_opportunity_score: number | null; candidate_fit_score: number; company_name: string | null; job_title: string | null }) =>
  JSON.stringify([row.hidden_opportunity_score, row.candidate_fit_score, row.company_name, row.job_title]);

describe.each(golden.cases)("golden search: $name", ({ profile, expected, momentum }) => {
  const { results, momentum: scores } = rankHiddenOpportunities(input, profile);

  test("same number of results", () => {
    expect(results.length).toBe(expected.length);
  });

  test("same order and scores for every result", () => {
    // Rows that tie on every sort key can come out in either order in
    // pandas, so compare each tied run as a group, matched by job URL.
    let start = 0;
    while (start < expected.length) {
      let end = start + 1;
      while (end < expected.length && key(expected[end]) === key(expected[start])) end += 1;
      const byUrl = (rows: (ExpectedRow | RankedOpportunity)[]) =>
        [...rows].sort((a, b) => String(a.job_url).localeCompare(String(b.job_url)));
      const want = byUrl(expected.slice(start, end)) as ExpectedRow[];
      const got = byUrl(results.slice(start, end)) as RankedOpportunity[];
      want.forEach((row, index) => {
        const actual = got[index];
        expect({
          company_name: actual.company_name,
          job_title: actual.job_title,
          location: actual.location,
          industry: actual.industry,
          job_url: actual.job_url,
          candidate_fit_score: actual.candidate_fit_score,
          hiring_momentum_score: actual.hiring_momentum_score,
          hidden_opportunity_score: actual.hidden_opportunity_score,
          family_match: actual.family_match,
          skill_match: actual.skill_match,
          industry_match: actual.industry_match,
          location_match: actual.location_match,
          explanation: explainOpportunity(actual, profile),
        }).toEqual(row);
      });
      start = end;
    }
  });

  test("same Hiring Momentum for every company", () => {
    expect(scores.size).toBe(Object.keys(momentum).length);
    for (const [companyId, want] of Object.entries(momentum)) {
      const got = scores.get(companyId);
      expect(got, companyId).toBeDefined();
      expect({
        id: companyId,
        previous: got!.previous_open,
        current: got!.current_open,
        newJobs: got!.new_jobs,
        newRelevant: got!.new_relevant,
        relevantChange: got!.relevant_change,
        components: [got!.new_relevant_component, got!.relevant_change_component, got!.job_growth_component, got!.new_jobs_component],
        score: got!.hiring_momentum_score,
      }).toEqual({
        id: companyId,
        previous: want.Previous_Open_Jobs,
        current: want.Current_Open_Jobs,
        newJobs: want.New_Jobs_7D,
        newRelevant: want.New_Relevant_Jobs_7D,
        relevantChange: want.Relevant_Job_Change_7D,
        components: [want.New_Relevant_Component, want.Relevant_Job_Change_Component, want.Job_Growth_Component, want.New_Jobs_Component],
        score: want.Hiring_Momentum_Score,
      });
    }
  });
});
