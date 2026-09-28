import pandas as pd

import candidate_fit
import hiring_momentum

FILE_PATH = "HiddenHire_Data.xlsx"

OUTPUT_COLUMNS = [
    "Company_Name",
    "Job_Title",
    "Location",
    "Industry",
    "Candidate_Fit_Score",
    "Hiring_Momentum_Score",
    "Hidden_Opportunity_Score",
    "Job_URL",
]


def rank_hidden_opportunities(
    target_roles,
    skills,
    preferred_industries,
    location,
    file_path=FILE_PATH,
):
    """Rank the latest jobs for one candidate profile.

    Candidate fit uses the supplied roles, skills, industries, and
    location. Hiring momentum stays the existing company-level score.
    Hidden_Opportunity_Score is 60% fit and 40% momentum.
    """
    user_profile = {
        "target_roles": list(target_roles),
        "skills": list(skills),
        "industries": list(preferred_industries),
        "location": location,
    }

    jobs = pd.read_excel(file_path, sheet_name="Job_Snapshots")
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    latest_date = jobs["Snapshot_Date"].max()
    latest_jobs = jobs[
        jobs["Snapshot_Date"] == latest_date
    ].copy()

    companies = pd.read_excel(file_path, sheet_name="Companies")

    fit = candidate_fit.score_candidate_fit(
        latest_jobs,
        companies,
        user_profile,
    )

    hiring_growth = hiring_momentum.calculate_hiring_momentum(jobs)
    momentum_scores = hiring_growth[
        ["Company_ID", "Hiring_Momentum_Score"]
    ].copy()
    momentum_scores["Company_ID"] = momentum_scores["Company_ID"].astype(str)
    momentum_scores = momentum_scores.drop_duplicates(subset=["Company_ID"])

    fit = fit.copy()
    fit["Company_ID"] = fit["Company_ID"].astype(str)

    ranked = fit.merge(
        momentum_scores,
        on="Company_ID",
        how="left",
    )

    ranked["Hidden_Opportunity_Score"] = (
        0.60 * ranked["Candidate_Fit_Score"]
        + 0.40 * ranked["Hiring_Momentum_Score"]
    ).round(1)

    ranked = ranked.sort_values(
        [
            "Hidden_Opportunity_Score",
            "Candidate_Fit_Score",
            "Company_Name",
            "Job_Title",
        ],
        ascending=[False, False, True, True],
    )

    return ranked[OUTPUT_COLUMNS].reset_index(drop=True)
