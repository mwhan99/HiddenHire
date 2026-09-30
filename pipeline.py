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

# Already calculated by candidate fit. Passed through for explanations only.
SIGNAL_COLUMNS = [
    "Family_Match",
    "Skill_Match",
    "Industry_Match",
    "Location_Match",
]


def is_active(value):
    """Blank counts as active. False, 0, "no", or "inactive" does not."""
    if value is None or pd.isna(value):
        return True
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "no", "n", "0", "inactive"}
    return bool(value)


def rank_hidden_opportunities(
    target_roles,
    skills,
    preferred_industries,
    location,
    file_path=FILE_PATH,
    experience_level="entry",
):
    """Rank the latest jobs for one candidate profile.

    Candidate fit uses the supplied roles, skills, industries,
    location, and experience level ("entry", "mid", or "senior").
    Hiring momentum is company-level, and its relevant-job
    signals count openings in the user's target role families.
    Hidden_Opportunity_Score is 60% fit and 40% momentum.
    """
    user_profile = {
        "target_roles": list(target_roles),
        "skills": list(skills),
        "industries": list(preferred_industries),
        "location": location,
        "experience_level": experience_level,
    }

    companies = pd.read_excel(file_path, sheet_name="Companies")

    jobs = pd.read_excel(file_path, sheet_name="Job_Snapshots")
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    # Leave out companies marked inactive. Otherwise a company that stops
    # being collected looks like it closed every job, and that drop would
    # set the scale for everyone else's momentum.
    active_ids = set(
        companies.loc[companies["Active"].apply(is_active), "Company_ID"]
        .astype(str)
    )
    jobs = jobs[jobs["Company_ID"].astype(str).isin(active_ids)].copy()

    latest_date = jobs["Snapshot_Date"].max()
    latest_jobs = jobs[
        jobs["Snapshot_Date"] == latest_date
    ].copy()

    fit = candidate_fit.score_candidate_fit(
        latest_jobs,
        companies,
        user_profile,
    )

    # Relevant-job momentum uses this user's target roles.
    hiring_growth = hiring_momentum.calculate_hiring_momentum(
        jobs,
        target_roles=user_profile["target_roles"],
    )
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

    return ranked[OUTPUT_COLUMNS + SIGNAL_COLUMNS].reset_index(drop=True)
