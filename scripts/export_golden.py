"""Export the scoring rules and "golden" results for the website's tests.

The website (web/) re-implements the per-search scoring in TypeScript.
This script writes two files so the two languages cannot drift apart:

  web/lib/scoring/config.json
      Role families, exclusions, seniority scores, and display labels,
      taken straight from candidate_fit.py and app.py.

  web/lib/scoring/__fixtures__/golden.json
      For a few fixed searches: the exact inputs the website receives
      from Supabase (the two compared snapshots, with the labels
      supabase_sync.py adds) and the results Python produces
      (pipeline.rank_hidden_opportunities, hiring momentum per company,
      and app.py's explanation sentence). The TypeScript tests must
      reproduce them.

Run it from the repository root with the same packages as production
(requirements.txt), after any change to the scoring code:

    python scripts/export_golden.py
"""

import ast
import gzip
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import candidate_fit  # noqa: E402
import hiring_momentum  # noqa: E402
import pipeline  # noqa: E402
import supabase_sync  # noqa: E402

WORKBOOK = os.path.join(ROOT, "HiddenHire_Data.xlsx")
SCORING_DIR = os.path.join(ROOT, "web", "lib", "scoring")

# Searches chosen to cover every role family, all three experience levels,
# remote and non-New York locations, symbols in skills ("c++", "a/b"), a
# level typed as a label ("Mid level"), and an empty industry list.
PROFILES = [
    {
        "name": "default analyst search",
        "target_roles": ["business analyst", "strategy analyst", "operations analyst"],
        "skills": ["SQL", "Excel", "Tableau", "Python"],
        "industries": ["fintech", "AI", "enterprise software"],
        "location": "New York",
        "experience_level": "entry",
    },
    {
        "name": "mid-level engineer",
        "target_roles": ["software engineer", "backend engineer", "full stack engineer"],
        "skills": ["Python", "TypeScript", "React", "AWS", "SQL", "Go"],
        "industries": ["AI", "developer tools"],
        "location": "New York",
        "experience_level": "mid",
    },
    {
        "name": "senior product and data, remote",
        "target_roles": ["product manager", "data scientist", "machine learning engineer"],
        "skills": ["Python", "SQL", "A/B testing", "statistics", "PyTorch"],
        "industries": ["healthtech", "AI"],
        "location": "Remote",
        "experience_level": "senior",
    },
    {
        "name": "entry finance and growth, San Francisco",
        "target_roles": ["financial analyst", "fp&a", "growth analyst", "marketing analyst"],
        "skills": ["Excel", "SQL", "financial modeling", "Looker", "C++"],
        "industries": ["fintech", "consumer", "healthcare"],
        "location": "San Francisco",
        "experience_level": "entry",
    },
    {
        "name": "operations roles, label-style level, no industries",
        "target_roles": ["revenue operations", "sales operations", "product operations", "data analyst"],
        "skills": ["Salesforce", "SQL"],
        "industries": [],
        "location": "nyc",
        "experience_level": "Mid level",
    },
]


def app_helpers():
    """Load explain_opportunity and FAMILY_LABELS from app.py without
    running the Streamlit page (importing app.py would draw the UI)."""
    wanted = {
        "FAMILY_LABELS", "join_phrases", "matched_family_labels", "row_value",
        "signal_above", "signal_at_least", "explain_opportunity",
    }
    with open(os.path.join(ROOT, "app.py")) as handle:
        tree = ast.parse(handle.read())
    nodes = [
        node for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name in wanted)
        or (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in wanted for target in node.targets))
    ]
    namespace = {"pd": pd, "candidate_fit": candidate_fit}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), namespace)
    return namespace


def clean(value):
    return supabase_sync.clean(value)


def main():
    helpers = app_helpers()

    # ---- config.json ---------------------------------------------------
    config = {
        "role_families": candidate_fit.ROLE_FAMILIES,
        "role_exclusions": candidate_fit.ROLE_EXCLUSIONS,
        "experience_levels": candidate_fit.EXPERIENCE_LEVELS,
        "seniority_scores": candidate_fit.SENIORITY_SCORES,
        "supported_roles": candidate_fit.supported_roles(),
        "family_labels": helpers["FAMILY_LABELS"],
    }
    with open(os.path.join(SCORING_DIR, "config.json"), "w") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")

    # ---- golden.json: inputs -------------------------------------------
    companies = pd.read_excel(WORKBOOK, sheet_name="Companies")
    jobs = pd.read_excel(WORKBOOK, sheet_name="Job_Snapshots")
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    active_ids = set(companies.loc[companies["Active"].apply(pipeline.is_active), "Company_ID"].astype(str))
    active_jobs = jobs[jobs["Company_ID"].astype(str).isin(active_ids)]
    dates = sorted(active_jobs["Snapshot_Date"].dt.normalize().unique())
    previous_date, current_date = hiring_momentum.choose_comparison_dates(dates)

    compared = jobs[jobs["Snapshot_Date"].dt.normalize().isin([previous_date, current_date])]
    job_rows = supabase_sync.job_snapshot_rows(compared)
    keep = ["snapshot_date", "company_id", "company_name", "job_id", "job_title",
            "location", "job_url", "role_families", "seniority"]
    job_rows = [{key: row[key] for key in keep} for row in job_rows]

    # Descriptions only matter for jobs that can match a role family; the
    # others are never scored. This keeps the file small.
    current_key = current_date.date().isoformat()
    descriptions = {}
    for row in compared.to_dict("records"):
        if pd.Timestamp(row["Snapshot_Date"]).date().isoformat() != current_key:
            continue
        if not supabase_sync.role_families(supabase_sync.text(row.get("Job_Title"))):
            continue
        key = f'{row["Company_ID"]}|{supabase_sync.job_id_text(row["Job_ID"])}'
        descriptions[key] = supabase_sync.text(row.get("Job_Description"))

    # ---- golden.json: expected results ---------------------------------
    cases = []
    for profile in PROFILES:
        results = pipeline.rank_hidden_opportunities(
            profile["target_roles"], profile["skills"], profile["industries"],
            profile["location"], file_path=WORKBOOK,
            experience_level=profile["experience_level"],
        )
        momentum = hiring_momentum.calculate_hiring_momentum(
            active_jobs, target_roles=profile["target_roles"],
        )
        search_profile = {key: profile[key] for key in
                          ["target_roles", "skills", "industries", "location", "experience_level"]}
        expected = []
        for row in results.to_dict("records"):
            entry = {key.lower(): clean(value) for key, value in row.items()}
            entry["explanation"] = helpers["explain_opportunity"](pd.Series(row), search_profile)
            expected.append(entry)
        cases.append({
            "name": profile["name"],
            "profile": search_profile,
            "expected": expected,
            "momentum": {
                str(row["Company_ID"]): {
                    key: clean(row[key]) for key in [
                        "Previous_Open_Jobs", "Current_Open_Jobs", "New_Jobs_7D",
                        "New_Relevant_Jobs_7D", "Relevant_Job_Change_7D",
                        "New_Relevant_Component", "Relevant_Job_Change_Component",
                        "Job_Growth_Component", "New_Jobs_Component", "Hiring_Momentum_Score",
                    ]
                }
                for row in momentum.to_dict("records")
            },
        })

    golden = {
        "generated_from": os.path.basename(WORKBOOK),
        "snapshot_dates": [pd.Timestamp(date).date().isoformat() for date in dates],
        "comparison": {"previous": previous_date.date().isoformat(), "current": current_key},
        "companies": [
            {
                "company_id": str(row["Company_ID"]),
                "company_name": supabase_sync.text(row["Company_Name"]),
                "industry": supabase_sync.text(row.get("Industry")),
                "active": pipeline.is_active(row.get("Active")),
            }
            for row in companies.to_dict("records")
        ],
        "jobs": job_rows,
        "descriptions": descriptions,
        "cases": cases,
    }
    os.makedirs(os.path.join(SCORING_DIR, "__fixtures__"), exist_ok=True)
    # Compressed, because job titles and descriptions make it a few MB.
    # mtime=0 keeps the file identical when nothing changed.
    path = os.path.join(SCORING_DIR, "__fixtures__", "golden.json.gz")
    data = json.dumps(golden, allow_nan=False, separators=(",", ":")).encode()
    with open(path, "wb") as handle:
        handle.write(gzip.compress(data, mtime=0))

    print(f"Wrote config.json and golden.json.gz ({os.path.getsize(path) / 1e6:.2f} MB compressed)")
    print(f"Comparison: {golden['comparison']['previous']} -> {golden['comparison']['current']}")
    print(f"Jobs: {len(job_rows)}, descriptions: {len(descriptions)}")
    for case in cases:
        print(f"  {case['name']}: {len(case['expected'])} results")


if __name__ == "__main__":
    main()
