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
        (
            "2026-09-21",
            [
                ("A", "1", "Business Analyst"),
                ("B", "5", "Account Executive"),
            ],
        ),
        (
            "2026-09-28",
            [
                ("A", "1", "Business Analyst"),
                ("A", "2", "Strategy Analyst"),
                ("B", "5", "Account Executive"),
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


def _company_rows(date, company, count, start=0, title="Operations Associate"):
    return [
        {
            "Snapshot_Date": date,
            "Company_ID": company,
            "Company_Name": company,
            "Job_ID": f"{company}-{start + i}",
            "Job_Title": title,
        }
        for i in range(count)
    ]


def test_growth_is_relative_to_company_size():
    rows = []
    # Small: 12 openings, adds 6. Big: 150 openings, adds 6.
    rows += _company_rows("2026-09-21", "Small", 12)
    rows += _company_rows("2026-09-28", "Small", 18)
    rows += _company_rows("2026-09-21", "Big", 150)
    rows += _company_rows("2026-09-28", "Big", 156)
    # A third company that stays flat, so the scale is not just two points.
    rows += _company_rows("2026-09-21", "Flat", 20)
    rows += _company_rows("2026-09-28", "Flat", 20)

    scores = hm.calculate_hiring_momentum(
        pd.DataFrame(rows), target_roles=["operations associate"]
    ).set_index("Company_ID")["Hiring_Momentum_Score"]

    assert scores["Small"] > scores["Big"] > scores["Flat"]


def test_newly_tracked_company_is_neutral():
    rows = []
    rows += _company_rows("2026-09-21", "Old", 10)
    rows += _company_rows("2026-09-28", "Old", 12)
    # "New" was added to the list this week: all 40 openings look new.
    rows += _company_rows("2026-09-28", "New", 40)

    result = hm.calculate_hiring_momentum(
        pd.DataFrame(rows), target_roles=["operations associate"]
    ).set_index("Company_ID")

    assert bool(result.loc["New", "Newly_Tracked"])
    assert result.loc["New", "Hiring_Momentum_Score"] == 50.0
    assert result.loc["Old", "Hiring_Momentum_Score"] > 50.0


def test_one_extreme_company_does_not_flatten_the_rest():
    values = pd.Series([0.0] + [0.1] * 9 + [5.0])
    scaled = hm.normalize_signal(values)
    # The 90th-percentile scale keeps typical growth well above neutral.
    assert scaled.iloc[1] > 90
    assert scaled.iloc[-1] == 100
    assert scaled.iloc[0] == 50
