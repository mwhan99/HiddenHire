import pandas as pd

import hiring_momentum as hm


def _dates(*values):
    return pd.to_datetime(list(values))


def test_compares_with_snapshot_about_a_week_earlier():
    previous, current = hm.choose_comparison_dates(
        _dates("2026-09-20", "2026-09-27", "2026-09-28", "2026-10-05")
    )
    assert previous == pd.Timestamp("2026-09-28")
    assert current == pd.Timestamp("2026-10-05")


def test_ignores_a_recent_extra_run():
    previous, current = hm.choose_comparison_dates(
        _dates("2026-09-28", "2026-10-05", "2026-10-07", "2026-10-12")
    )
    assert previous == pd.Timestamp("2026-10-05")
    assert current == pd.Timestamp("2026-10-12")


def test_falls_back_while_history_is_short():
    previous, current = hm.choose_comparison_dates(
        _dates("2026-09-27", "2026-09-28")
    )
    assert previous == pd.Timestamp("2026-09-27")
    assert current == pd.Timestamp("2026-09-28")


def _snapshots():
    rows = []
    for date, jobs in [
        ("2026-09-21", [("A", "1", "Business Analyst")]),
        (
            "2026-09-28",
            [
                ("A", "1", "Business Analyst"),
                ("A", "2", "Strategy Analyst"),
                ("B", "3", "Software Engineer"),
                ("B", "4", "Backend Engineer"),
            ],
        ),
    ]:
        for company, job_id, title in jobs:
            rows.append(
                {
                    "Snapshot_Date": date,
                    "Company_ID": company,
                    "Company_Name": company,
                    "Job_ID": job_id,
                    "Job_Title": title,
                }
            )
    return pd.DataFrame(rows)


def test_relevant_jobs_follow_the_searched_roles():
    analyst = hm.calculate_hiring_momentum(
        _snapshots(), target_roles=["business analyst"]
    ).set_index("Company_ID")
    engineer = hm.calculate_hiring_momentum(
        _snapshots(), target_roles=["software engineer"]
    ).set_index("Company_ID")

    assert analyst.loc["A", "New_Relevant_Jobs_7D"] == 0  # strategy is another family
    assert engineer.loc["B", "New_Relevant_Jobs_7D"] == 2
    assert engineer.loc["B", "Hiring_Momentum_Score"] > analyst.loc["B", "Hiring_Momentum_Score"]
