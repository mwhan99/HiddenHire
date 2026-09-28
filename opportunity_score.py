import pandas as pd

FILE_PATH = "HiddenHire_Data.xlsx"

import hiring_momentum


def main():

    # ==========================================
    # LOAD CANDIDATE FIT RESULTS
    # ==========================================

    candidate_fit = pd.read_excel(
        FILE_PATH,
        sheet_name="Candidate_Fit"
    )

    candidate_fit["Company_ID"] = candidate_fit["Company_ID"].astype(str)

    print("=== CANDIDATE FIT DATA LOADED ===")
    print("Jobs:", len(candidate_fit))
    print("Companies:", candidate_fit["Company_ID"].nunique())

    print("\nColumns:")
    print(candidate_fit.columns.tolist())

    print("\nTop 10 Candidate Fit Jobs:")
    print(
        candidate_fit[
            [
                "Company_Name",
                "Job_Title",
                "Location",
                "Candidate_Fit_Score"
            ]
        ]
        .sort_values("Candidate_Fit_Score", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    # ==========================================
    # LOAD HIRING BASELINE
    # ==========================================

    jobs = pd.read_excel(
        FILE_PATH,
        sheet_name="Job_Snapshots"
    )

    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    latest_date = jobs["Snapshot_Date"].max()

    latest_jobs = jobs[
        jobs["Snapshot_Date"] == latest_date
    ].copy()

    company_hiring = (
        latest_jobs
        .groupby(["Company_ID", "Company_Name"])
        .size()
        .reset_index(name="Current_Jobs")
    )

    company_hiring["Company_ID"] = company_hiring["Company_ID"].astype(str)

    print("\n=== HIRING BASELINE ===")
    print("Snapshot Date:", latest_date.date())
    print("Companies:", len(company_hiring))

    print(
        company_hiring
        .sort_values("Current_Jobs", ascending=False)
        .head(15)
        .to_string(index=False)
    )

    # ==========================================
    # MERGE CANDIDATE FIT + HIRING BASELINE
    # ==========================================

    opportunities = candidate_fit.merge(
        company_hiring[
            ["Company_ID", "Current_Jobs"]
        ],
        on="Company_ID",
        how="left"
    )

    print("\n=== OPPORTUNITY MERGE CHECK ===")

    print(
        opportunities[
            [
                "Company_Name",
                "Job_Title",
                "Candidate_Fit_Score",
                "Current_Jobs"
            ]
        ]
        .sort_values("Candidate_Fit_Score", ascending=False)
        .head(15)
        .to_string(index=False)
    )

    print("\nJobs after merge:", len(opportunities))
    print(
        "Jobs missing hiring data:",
        opportunities["Current_Jobs"].isna().sum()
    )

    # ==========================================
    # MERGE HIRING MOMENTUM
    # Reuse the company-level score already calculated
    # in hiring_momentum.py. A left join keeps every
    # candidate-fit job.
    # ==========================================

    hiring_growth = hiring_momentum.calculate_hiring_momentum(jobs)

    momentum_scores = hiring_growth[
        ["Company_ID", "Hiring_Momentum_Score"]
    ].copy()

    momentum_scores["Company_ID"] = momentum_scores["Company_ID"].astype(str)

    duplicate_momentum_companies = (
        momentum_scores["Company_ID"].duplicated().sum()
    )

    momentum_scores = momentum_scores.drop_duplicates(
        subset=["Company_ID"]
    )

    jobs_before_momentum_merge = len(opportunities)

    opportunities = opportunities.merge(
        momentum_scores,
        on="Company_ID",
        how="left",
    )

    jobs_after_momentum_merge = len(opportunities)
    jobs_missing_momentum = (
        opportunities["Hiring_Momentum_Score"].isna().sum()
    )

    print("\n=== MOMENTUM MERGE CHECK ===")
    print("Candidate-fit jobs:", len(candidate_fit))
    print("Jobs before momentum merge:", jobs_before_momentum_merge)
    print("Jobs after momentum merge:", jobs_after_momentum_merge)
    print(
        "Duplicate momentum companies:",
        duplicate_momentum_companies,
    )
    print("Jobs missing Hiring_Momentum_Score:", jobs_missing_momentum)

    if jobs_after_momentum_merge == len(candidate_fit):
        print("No candidate-fit jobs were lost or duplicated.")
    else:
        print(
            "Job count changed by",
            jobs_after_momentum_merge - len(candidate_fit),
        )

    candidate_fit_unchanged = (
        opportunities["Candidate_Fit_Score"].tolist()
        == candidate_fit["Candidate_Fit_Score"].tolist()
    )

    print("Candidate_Fit_Score unchanged:", candidate_fit_unchanged)

    # ==========================================
    # HIDDEN OPPORTUNITY SCORE
    # 60% candidate fit, 40% hiring momentum
    # ==========================================

    opportunities["Hidden_Opportunity_Score"] = (
        0.60 * opportunities["Candidate_Fit_Score"]
        + 0.40 * opportunities["Hiring_Momentum_Score"]
    ).round(1)

    opportunities["Job_Growth_7D"] = pd.NA
    opportunities["Opportunity_Score"] = (
        opportunities["Hidden_Opportunity_Score"]
    )

    hidden_opportunities = opportunities[
        [
            "Snapshot_Date",
            "Company_ID",
            "Company_Name",
            "Job_ID",
            "Job_Title",
            "Location",
            "Industry",
            "Job_URL",
            "Candidate_Fit_Score",
            "Hiring_Momentum_Score",
            "Hidden_Opportunity_Score",
            "Current_Jobs",
            "Job_Growth_7D",
            "Opportunity_Score",
        ]
    ].copy()

    hidden_opportunities = hidden_opportunities.sort_values(
        [
            "Hidden_Opportunity_Score",
            "Candidate_Fit_Score",
            "Company_Name",
            "Job_Title",
        ],
        ascending=[False, False, True, True],
    )

    scored = hidden_opportunities["Hidden_Opportunity_Score"].dropna()
    scores_outside_range = ((scored < 0) | (scored > 100)).sum()

    print("\n=== HIDDEN OPPORTUNITY VALIDATION ===")
    print("Scored jobs:", len(scored))
    print("Lowest score:", scored.min() if len(scored) else None)
    print("Highest score:", scored.max() if len(scored) else None)
    print("Scores outside 0–100:", scores_outside_range)

    print("\n=== TOP 15 HIDDEN OPPORTUNITIES ===")

    print(
        hidden_opportunities[
            [
                "Company_Name",
                "Job_Title",
                "Candidate_Fit_Score",
                "Hiring_Momentum_Score",
                "Hidden_Opportunity_Score",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    # ==========================================
    # SAVE HIDDEN OPPORTUNITIES
    # ==========================================

    with pd.ExcelWriter(
        FILE_PATH,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:
        hidden_opportunities.to_excel(
            writer,
            sheet_name="Hidden_Opportunities",
            index=False
        )

    print("\n=== HIDDEN OPPORTUNITIES SAVED ===")
    print("Jobs saved:", len(hidden_opportunities))
    print("Sheet: Hidden_Opportunities")

if __name__ == "__main__":
    main()
