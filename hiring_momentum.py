import pandas as pd

FILE_PATH = "HiddenHire_Data.xlsx"

# ==========================================
# RELEVANT ROLES
# Role families, exclusions, and family-match rules come from
# candidate_fit.py so the two files cannot drift apart.
# A job is relevant when its family match would be greater than 0.
# ==========================================

from candidate_fit import (  # noqa: E402
    ROLE_EXCLUSIONS,
    ROLE_FAMILIES,
    calculate_family_match,
    find_role_families,
)

# Default roles for the command-line report. The app passes the
# user's own target roles into calculate_hiring_momentum instead.
TARGET_ROLES = [
    "business analyst",
    "strategy analyst",
    "operations analyst",
]

# ==========================================
# COMPARISON WINDOW
# Momentum compares the latest snapshot with the earlier snapshot
# closest to TARGET_GAP_DAYS before it. Snapshots fewer than
# MIN_GAP_DAYS earlier are ignored, so an extra manual run does not
# shrink the comparison to a day or two.
# ==========================================

TARGET_GAP_DAYS = 7
MIN_GAP_DAYS = 5


def choose_comparison_dates(snapshot_dates):
    """Return (previous_date, current_date) for the momentum comparison.

    Uses the earlier snapshot closest to TARGET_GAP_DAYS before the
    latest one, among snapshots at least MIN_GAP_DAYS earlier. If no
    snapshot is that old yet, falls back to the one just before the
    latest, so the app still works while history builds up.
    """
    dates = sorted(pd.Timestamp(d) for d in snapshot_dates)
    current_date = dates[-1]
    earlier = [
        d for d in dates[:-1]
        if (current_date - d).days >= MIN_GAP_DAYS
    ]
    if not earlier:
        return dates[-2], current_date

    target = current_date - pd.Timedelta(days=TARGET_GAP_DAYS)
    previous_date = min(
        earlier,
        key=lambda d: (abs((d - target).days), -d.value),
    )
    return previous_date, current_date


def normalize_signal(values):
    """Scale one signal to 0–100. A flat signal scores 50.

    The largest absolute value among tracked companies sets the scale.
    Positive values move toward 100. Negative values move toward 0.
    A decline therefore stays below a company with no change.
    """
    values = values.fillna(0)
    max_abs = values.abs().max()

    if pd.isna(max_abs) or max_abs == 0:
        return pd.Series(50.0, index=values.index)

    component = 50 + 50 * (values / max_abs)
    return component.clip(0, 100)


def calculate_hiring_momentum(jobs, report=False, target_roles=None):
    """Return the company hiring table, including Hiring_Momentum_Score.

    target_roles decides which openings count as relevant for the
    relevant-job signals. The app passes the user's target roles;
    when it is None, TARGET_ROLES is used.
    Passing report=True prints the same momentum report as the script.
    This function does not write the Excel workbook.
    """
    jobs = jobs.copy()
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])
    if target_roles is None:
        target_roles = TARGET_ROLES
    user_role_families = find_role_families(target_roles)
    hiring_growth = None

    def _report(*args, **kwargs):
        if report:
            print(*args, **kwargs)

    # ==========================================
    # CHECK HISTORICAL SNAPSHOT AVAILABILITY
    # ==========================================

    snapshot_dates = sorted(
        jobs["Snapshot_Date"].dt.normalize().unique()
    )

    _report("\n=== SNAPSHOT HISTORY CHECK ===")
    _report("Number of snapshot dates:", len(snapshot_dates))

    for date in snapshot_dates:
        _report(pd.Timestamp(date).date())

    if len(snapshot_dates) < 2:
        _report("\nNot enough historical data to calculate hiring growth yet.")
        _report("A second snapshot is required before Hiring Momentum can be calculated.")
    else:
        _report("\nHistorical data available. Hiring growth can be calculated.")

    # ==========================================
    # CALCULATE 7-DAY JOB GROWTH
    # ==========================================

    if len(snapshot_dates) >= 2:

        previous_date, current_date = choose_comparison_dates(
            snapshot_dates
        )
        gap_days = (current_date - previous_date).days
        if gap_days < MIN_GAP_DAYS:
            _report(
                f"\nOnly {gap_days} day(s) between the compared snapshots. "
                f"Momentum is more reliable once a snapshot at least "
                f"{MIN_GAP_DAYS} days old exists."
            )

        current_jobs = jobs[
            jobs["Snapshot_Date"].dt.normalize() == current_date
        ]

        previous_jobs = jobs[
            jobs["Snapshot_Date"].dt.normalize() == previous_date
        ]

        current_counts = (
            current_jobs
            .groupby(["Company_ID", "Company_Name"])
            .agg(Current_Open_Jobs=("Job_ID", "nunique"))
            .reset_index()
        )

        previous_counts = (
            previous_jobs
            .groupby(["Company_ID", "Company_Name"])
            .agg(Previous_Open_Jobs=("Job_ID", "nunique"))
            .reset_index()
        )

        hiring_growth = pd.merge(
            current_counts,
            previous_counts,
            on=["Company_ID", "Company_Name"],
            how="outer"
        )

        hiring_growth["Current_Open_Jobs"] = (
            hiring_growth["Current_Open_Jobs"].fillna(0).astype(int)
        )

        hiring_growth["Previous_Open_Jobs"] = (
            hiring_growth["Previous_Open_Jobs"].fillna(0).astype(int)
        )

        hiring_growth["Job_Change_7D"] = (
            hiring_growth["Current_Open_Jobs"]
            - hiring_growth["Previous_Open_Jobs"]
        )

        hiring_growth["Job_Growth_7D_Pct"] = (
            hiring_growth["Job_Change_7D"]
            / hiring_growth["Previous_Open_Jobs"]
            * 100
        )

        hiring_growth.loc[
            hiring_growth["Previous_Open_Jobs"] == 0,
            "Job_Growth_7D_Pct"
        ] = pd.NA

        hiring_growth["Job_Growth_7D_Pct"] = (
            hiring_growth["Job_Growth_7D_Pct"].round(1)
        )

        hiring_growth = hiring_growth.sort_values(
            "Job_Change_7D",
            ascending=False
        )

        _report("\n=== 7-DAY HIRING GROWTH ===")
        _report("Previous snapshot:", previous_date.date())
        _report("Current snapshot:", current_date.date())

        _report(
            hiring_growth[
                [
                    "Company_Name",
                    "Previous_Open_Jobs",
                    "Current_Open_Jobs",
                    "Job_Change_7D",
                    "Job_Growth_7D_Pct"
                ]
            ].to_string(index=False)
        )

        # ==========================================
        # JOB-LEVEL CHANGES BETWEEN SNAPSHOTS
        # ==========================================

        def jobs_with_ids(snapshot):
            rows = snapshot.dropna(subset=["Job_ID"]).copy()
            # Compare IDs as text so numeric and text IDs match reliably.
            rows["Job_ID_Key"] = rows["Job_ID"].astype(str).str.strip()
            rows = rows[rows["Job_ID_Key"] != ""]
            rows = rows.drop_duplicates(subset=["Company_ID", "Job_ID_Key"])
            return rows

        current_job_rows = jobs_with_ids(current_jobs)
        previous_job_rows = jobs_with_ids(previous_jobs)

        current_job_rows["Job_Key"] = list(
            zip(current_job_rows["Company_ID"], current_job_rows["Job_ID_Key"])
        )
        previous_job_rows["Job_Key"] = list(
            zip(previous_job_rows["Company_ID"], previous_job_rows["Job_ID_Key"])
        )

        current_keys = set(current_job_rows["Job_Key"])
        previous_keys = set(previous_job_rows["Job_Key"])

        new_jobs = current_job_rows[
            ~current_job_rows["Job_Key"].isin(previous_keys)
        ].copy()

        closed_jobs = previous_job_rows[
            ~previous_job_rows["Job_Key"].isin(current_keys)
        ].copy()

        job_list_columns = [
            column
            for column in [
                "Job_ID",
                "Company_ID",
                "Company_Name",
                "Job_Title",
                "Location",
                "Job_URL",
            ]
            if column in current_job_rows.columns
        ]

        sort_columns = [
            column
            for column in ["Company_Name", "Job_Title"]
            if column in job_list_columns
        ]

        new_jobs = (
            new_jobs[job_list_columns]
            .sort_values(sort_columns)
            .reset_index(drop=True)
        )

        closed_jobs = (
            closed_jobs[job_list_columns]
            .sort_values(sort_columns)
            .reset_index(drop=True)
        )

        new_job_counts = (
            new_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="New_Jobs_7D")
        )

        closed_job_counts = (
            closed_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="Closed_Jobs_7D")
        )

        hiring_growth = hiring_growth.merge(
            new_job_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        hiring_growth = hiring_growth.merge(
            closed_job_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        hiring_growth["New_Jobs_7D"] = (
            hiring_growth["New_Jobs_7D"].fillna(0).astype(int)
        )

        hiring_growth["Closed_Jobs_7D"] = (
            hiring_growth["Closed_Jobs_7D"].fillna(0).astype(int)
        )

        hiring_growth["Net_Job_Change_7D"] = (
            hiring_growth["New_Jobs_7D"]
            - hiring_growth["Closed_Jobs_7D"]
        )

        _report("\n=== JOB-LEVEL CHANGES ===")
        _report(
            hiring_growth[
                [
                    "Company_Name",
                    "New_Jobs_7D",
                    "Closed_Jobs_7D",
                    "Net_Job_Change_7D",
                    "Job_Change_7D",
                ]
            ].to_string(index=False)
        )

        mismatch = hiring_growth[
            hiring_growth["Net_Job_Change_7D"]
            != hiring_growth["Job_Change_7D"]
        ]

        if mismatch.empty:
            _report("\nNet_Job_Change_7D matches Job_Change_7D for every company.")
        else:
            _report(
                "\nNet_Job_Change_7D does not match Job_Change_7D for",
                len(mismatch),
                "companies.",
            )
            _report(
                mismatch[
                    [
                        "Company_Name",
                        "New_Jobs_7D",
                        "Closed_Jobs_7D",
                        "Net_Job_Change_7D",
                        "Job_Change_7D",
                    ]
                ].to_string(index=False)
            )

        _report("\n=== NEWLY ADDED JOBS ===")
        _report("New jobs:", len(new_jobs))
        _report(new_jobs.to_string(index=False))

        _report("\n=== CLOSED JOBS ===")
        _report("Closed jobs:", len(closed_jobs))
        _report(closed_jobs.to_string(index=False))

        # ==========================================
        # RELEVANT JOB HIRING ACTIVITY
        # ==========================================

        _report("\n=== RELEVANT ROLE FAMILIES ===")
        _report(user_role_families)

        current_job_rows["Is_Relevant"] = current_job_rows["Job_Title"].apply(
            lambda title: calculate_family_match(title, user_role_families) > 0
        )

        previous_job_rows["Is_Relevant"] = previous_job_rows["Job_Title"].apply(
            lambda title: calculate_family_match(title, user_role_families) > 0
        )

        current_relevant_jobs = current_job_rows[
            current_job_rows["Is_Relevant"]
        ].copy()

        previous_relevant_jobs = previous_job_rows[
            previous_job_rows["Is_Relevant"]
        ].copy()

        # New or closed is based on Job_ID, same as the overall job comparison.
        # Relevance comes from the job title in that snapshot.
        new_relevant_jobs = current_relevant_jobs[
            ~current_relevant_jobs["Job_Key"].isin(previous_keys)
        ].copy()

        closed_relevant_jobs = previous_relevant_jobs[
            ~previous_relevant_jobs["Job_Key"].isin(current_keys)
        ].copy()

        current_relevant_counts = (
            current_relevant_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="Current_Relevant_Jobs")
        )

        previous_relevant_counts = (
            previous_relevant_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="Previous_Relevant_Jobs")
        )

        new_relevant_counts = (
            new_relevant_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="New_Relevant_Jobs_7D")
        )

        closed_relevant_counts = (
            closed_relevant_jobs
            .groupby(["Company_ID", "Company_Name"])
            .size()
            .reset_index(name="Closed_Relevant_Jobs_7D")
        )

        hiring_growth = hiring_growth.merge(
            previous_relevant_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        hiring_growth = hiring_growth.merge(
            current_relevant_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        hiring_growth = hiring_growth.merge(
            new_relevant_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        hiring_growth = hiring_growth.merge(
            closed_relevant_counts,
            on=["Company_ID", "Company_Name"],
            how="left",
        )

        for column in [
            "Previous_Relevant_Jobs",
            "Current_Relevant_Jobs",
            "New_Relevant_Jobs_7D",
            "Closed_Relevant_Jobs_7D",
        ]:
            hiring_growth[column] = (
                hiring_growth[column].fillna(0).astype(int)
            )

        hiring_growth["Relevant_Job_Change_7D"] = (
            hiring_growth["New_Relevant_Jobs_7D"]
            - hiring_growth["Closed_Relevant_Jobs_7D"]
        )

        hiring_growth["Relevant_Job_Growth_7D_Pct"] = (
            hiring_growth["Relevant_Job_Change_7D"]
            / hiring_growth["Previous_Relevant_Jobs"]
            * 100
        )

        hiring_growth.loc[
            hiring_growth["Previous_Relevant_Jobs"] == 0,
            "Relevant_Job_Growth_7D_Pct"
        ] = pd.NA

        hiring_growth["Relevant_Job_Growth_7D_Pct"] = (
            hiring_growth["Relevant_Job_Growth_7D_Pct"].round(1)
        )

        relevant_activity = hiring_growth.sort_values(
            ["New_Relevant_Jobs_7D", "Relevant_Job_Change_7D"],
            ascending=False
        )

        _report("\n=== RELEVANT JOB HIRING ACTIVITY ===")
        _report(
            relevant_activity[
                [
                    "Company_Name",
                    "Previous_Relevant_Jobs",
                    "Current_Relevant_Jobs",
                    "New_Relevant_Jobs_7D",
                    "Closed_Relevant_Jobs_7D",
                    "Relevant_Job_Change_7D",
                    "Relevant_Job_Growth_7D_Pct",
                ]
            ].to_string(index=False)
        )

        change_mismatch = hiring_growth[
            hiring_growth["Relevant_Job_Change_7D"]
            != (
                hiring_growth["New_Relevant_Jobs_7D"]
                - hiring_growth["Closed_Relevant_Jobs_7D"]
            )
        ]

        infinite_growth = hiring_growth[
            "Relevant_Job_Growth_7D_Pct"
        ].isin([float("inf"), float("-inf")]).sum()

        zero_previous = hiring_growth["Previous_Relevant_Jobs"] == 0
        numbered_zero_previous = (
            zero_previous
            & hiring_growth["Relevant_Job_Growth_7D_Pct"].notna()
        ).sum()

        _report("\n=== RELEVANT JOB VALIDATION ===")

        if change_mismatch.empty:
            _report(
                "Relevant_Job_Change_7D equals "
                "New_Relevant_Jobs_7D - Closed_Relevant_Jobs_7D "
                "for every company."
            )
        else:
            _report(
                "Relevant job change does not reconcile for",
                len(change_mismatch),
                "companies.",
            )

        _report("Infinite relevant growth values:", infinite_growth)
        _report(
            "Companies with zero previous relevant jobs "
            "and a numeric growth rate:",
            numbered_zero_previous,
        )
        _report("New relevant jobs:", len(new_relevant_jobs))
        _report("Closed relevant jobs:", len(closed_relevant_jobs))

        _report("\n=== NEW RELEVANT JOBS ===")
        new_relevant_list = new_relevant_jobs[
            [
                column
                for column in ["Company_Name", "Job_Title", "Location"]
                if column in new_relevant_jobs.columns
            ]
        ].sort_values(["Company_Name", "Job_Title"])

        _report(new_relevant_list.to_string(index=False))

        # ==========================================
        # HIRING MOMENTUM SCORE
        # 40% new relevant jobs
        # 25% net relevant job change
        # 20% overall job growth rate
        # 15% new job postings
        # ==========================================

        hiring_growth["New_Relevant_Component"] = normalize_signal(
            hiring_growth["New_Relevant_Jobs_7D"]
        ).round(1)

        hiring_growth["Relevant_Job_Change_Component"] = normalize_signal(
            hiring_growth["Relevant_Job_Change_7D"]
        ).round(1)

        hiring_growth["Job_Growth_Component"] = normalize_signal(
            hiring_growth["Job_Growth_7D_Pct"]
        ).round(1)

        hiring_growth["New_Jobs_Component"] = normalize_signal(
            hiring_growth["New_Jobs_7D"]
        ).round(1)

        hiring_growth["Hiring_Momentum_Score"] = (
            hiring_growth["New_Relevant_Component"] * 0.40
            + hiring_growth["Relevant_Job_Change_Component"] * 0.25
            + hiring_growth["Job_Growth_Component"] * 0.20
            + hiring_growth["New_Jobs_Component"] * 0.15
        ).round(1)

        momentum_ranking = hiring_growth.sort_values(
            ["Hiring_Momentum_Score", "New_Relevant_Jobs_7D"],
            ascending=False
        )

        _report("\n=== HIRING MOMENTUM SCORE ===")
        _report(
            momentum_ranking[
                [
                    "Company_Name",
                    "New_Relevant_Jobs_7D",
                    "New_Relevant_Component",
                    "Relevant_Job_Change_7D",
                    "Relevant_Job_Change_Component",
                    "Job_Growth_7D_Pct",
                    "Job_Growth_Component",
                    "New_Jobs_7D",
                    "New_Jobs_Component",
                    "Hiring_Momentum_Score",
                ]
            ].to_string(index=False)
        )

        score = hiring_growth["Hiring_Momentum_Score"]
        scores_outside_range = ((score < 0) | (score > 100)).sum()

        negative_relevant_change = hiring_growth["Relevant_Job_Change_7D"] < 0
        relevant_decline_not_penalized = (
            negative_relevant_change
            & (hiring_growth["Relevant_Job_Change_Component"] >= 50)
        ).sum()

        negative_growth = hiring_growth["Job_Growth_7D_Pct"].fillna(0) < 0
        growth_decline_not_penalized = (
            negative_growth
            & (hiring_growth["Job_Growth_Component"] >= 50)
        ).sum()

        zero_relevant_component = hiring_growth.loc[
            hiring_growth["New_Relevant_Jobs_7D"] == 0,
            "New_Relevant_Component",
        ]
        positive_relevant_component = hiring_growth.loc[
            hiring_growth["New_Relevant_Jobs_7D"] > 0,
            "New_Relevant_Component",
        ]

        flat_open_jobs = hiring_growth[
            (hiring_growth["Job_Change_7D"] == 0)
            & (hiring_growth["New_Jobs_7D"] > 0)
        ]

        _report("\n=== HIRING MOMENTUM VALIDATION ===")
        _report("Lowest score:", score.min())
        _report("Highest score:", score.max())
        _report("Scores outside 0–100:", scores_outside_range)
        _report(
            "Negative relevant changes scored at or above neutral:",
            relevant_decline_not_penalized,
        )
        _report(
            "Negative growth rates scored at or above neutral:",
            growth_decline_not_penalized,
        )

        if (
            len(zero_relevant_component) > 0
            and len(positive_relevant_component) > 0
            and positive_relevant_component.min() > zero_relevant_component.max()
        ):
            _report(
                "Companies that added a relevant job score above "
                "companies that added none on the relevant-creation component."
            )
        else:
            _report(
                "Relevant-creation component did not give added jobs "
                "a higher score than companies with none."
            )

        _report(
            "Companies with flat open-job counts but new postings:",
            len(flat_open_jobs),
        )
        if len(flat_open_jobs) == 0:
            _report("No flat-count companies had new postings to check.")
        elif (flat_open_jobs["New_Jobs_Component"] > 50).all():
            _report(
                "Those companies still score above neutral "
                "on the new-jobs component."
            )
        else:
            _report(
                "Some flat-count companies did not score above neutral "
                "on the new-jobs component."
            )

    return hiring_growth


def main():
    # Load historical job snapshots
    jobs = pd.read_excel(FILE_PATH, sheet_name="Job_Snapshots")

    # Make sure Snapshot_Date is treated as a date
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    latest_date = jobs["Snapshot_Date"].max()

    print("Latest snapshot date:", latest_date.date())

    # Only use the latest snapshot
    latest_jobs = jobs[jobs["Snapshot_Date"] == latest_date]

    # Count current open jobs for each company
    company_hiring = (
        latest_jobs
        .groupby(["Company_ID", "Company_Name"])
        .agg(
            Current_Open_Jobs=("Job_ID", "nunique")
        )
        .reset_index()
    )

    # Sort companies by number of open jobs
    company_hiring = company_hiring.sort_values(
        "Current_Open_Jobs",
        ascending=False
    )

    print("\n=== CURRENT COMPANY HIRING ===")
    print(company_hiring.to_string(index=False))

    print("\nCompanies tracked:", len(company_hiring))
    print("Total current jobs:", company_hiring["Current_Open_Jobs"].sum())

    print("\nSnapshot dates:")
    print(jobs["Snapshot_Date"].value_counts().sort_index())

    # ==========================================
    # SAVE DAY 1 HIRING BASELINE
    # ==========================================

    baseline = company_hiring.copy()

    baseline.insert(0, "Snapshot_Date", latest_date)

    baseline = baseline[
        [
            "Snapshot_Date",
            "Company_ID",
            "Company_Name",
            "Current_Open_Jobs"
        ]
    ]

    print("\n=== HIRING BASELINE ===")
    print(baseline.to_string(index=False))

    # Save baseline to Excel
    with pd.ExcelWriter(
        FILE_PATH,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:
        baseline.to_excel(
            writer,
            sheet_name="Hiring_Baseline",
            index=False
        )

    print("\nHiring_Baseline saved successfully!")

    calculate_hiring_momentum(jobs, report=True)


if __name__ == "__main__":
    main()
