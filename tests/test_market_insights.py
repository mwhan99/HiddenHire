import pandas as pd

import market_insights as mi


def test_classify_function():
    cases = {
        "Senior Backend Engineer": "Engineering",
        "Data Scientist, Finance": "Data & Analytics",
        "Business Analyst": "Data & Analytics",
        "Revenue Operations Analyst": "Operations & Strategy",
        "Legal Operations and Contracts Specialist": "Finance, Legal & Compliance",
        "Senior Revenue Accountant": "Finance, Legal & Compliance",
        "Talent Acquisition | Recruiter, Financial Services": "People & Recruiting",
        "Enterprise Account Executive, EMEA": "Sales & Partnerships",
        "Customer Success Manager": "Customer Success & Support",
        "Product Designer": "Design",
        "Product Marketing Manager": "Marketing & Creative",
        "Senior Product Manager, Platform": "Product",
        "Psychiatrist (MD / DO)": "Clinical & Care",
        "General Application": "Other",
    }
    for title, function in cases.items():
        assert mi.classify_function(title) == function, title
    assert mi.classify_function(None) == "Other"


def test_industry_tags():
    assert mi.industry_tags("AI / FinTech / FP&A Software") == ["AI", "FinTech", "FP&A Software"]
    assert mi.industry_tags(None) == []


def _rows(date, company, job_ids, title="Software Engineer"):
    return [
        {
            "Snapshot_Date": date,
            "Company_ID": company,
            "Company_Name": f"Company {company}",
            "Job_ID": job_id,
            "Job_Title": title,
        }
        for job_id in job_ids
    ]


def _history():
    rows = []
    # Week 1
    rows += _rows("2026-09-28", "A", range(1, 11))                 # 10 roles
    rows += _rows("2026-09-28", "B", range(100, 120), "Account Executive")  # 20 roles
    rows += _rows("2026-09-28", "C", range(200, 205))              # 5 roles
    rows += _rows("2026-09-28", "X", range(300, 303))              # inactive
    # A manual run two days later should not be used for comparison.
    rows += _rows("2026-09-30", "A", range(1, 11))
    # Week 2: A grows 10 -> 14 (2 closed, 6 new), B shrinks 20 -> 15,
    # C unchanged, D is newly added.
    rows += _rows("2026-10-05", "A", list(range(3, 11)) + list(range(11, 17)))
    rows += _rows("2026-10-05", "B", range(100, 115), "Account Executive")
    rows += _rows("2026-10-05", "C", range(200, 205))
    rows += _rows("2026-10-05", "D", range(400, 410))
    jobs = pd.DataFrame(rows)
    companies = pd.DataFrame({
        "Company_ID": ["A", "B", "C", "D", "X"],
        "Company_Name": ["Company A", "Company B", "Company C", "Company D", "Company X"],
        "Industry": ["AI / FinTech", "FinTech", "HealthTech", "AI", "AI"],
        "Active": [True, True, True, True, False],
    })
    return mi.prepare_history(jobs, companies)


def test_inactive_companies_are_left_out():
    jobs, companies = _history()
    assert "X" not in set(jobs["Company_ID"])
    assert "X" not in set(companies["Company_ID"])


def test_comparison_uses_week_old_snapshot():
    jobs, _ = _history()
    previous, current, gap = mi.comparison_window(jobs)
    assert previous == pd.Timestamp("2026-09-28")
    assert current == pd.Timestamp("2026-10-05")
    assert gap == 7


def test_headline_numbers():
    jobs, _ = _history()
    summary = mi.headline(jobs)
    assert summary["open_roles"] == 14 + 15 + 5 + 10
    assert summary["previous_open_roles"] == 10 + 20 + 5
    # New: A's 6 + D's 10. Closed: A's 2 + B's 5.
    assert summary["new_roles"] == 16
    assert summary["closed_roles"] == 7
    assert summary["companies_growing"] == 1   # A (D is newly tracked)
    assert summary["companies_slowing"] == 1   # B


def test_company_movers():
    jobs, companies = _history()
    movers = mi.company_movers(jobs, companies).set_index("Company_ID")
    assert "D" not in movers.index  # newly tracked
    assert movers.loc["A", "Net_Change"] == 4
    assert movers.loc["A", "New_Roles"] == 6
    assert movers.loc["A", "Closed_Roles"] == 2
    assert movers.loc["A", "Change_Pct"] == 40
    assert movers.loc["B", "Net_Change"] == -5
    assert movers.loc["A", "Industry"] == "AI / FinTech"

    growing = mi.fastest_growing(movers.reset_index())
    slowing = mi.slowing_down(movers.reset_index())
    assert list(growing["Company_ID"]) == ["A"]
    assert list(slowing["Company_ID"]) == ["B"]


def test_roles_by_function():
    jobs, _ = _history()
    table = mi.roles_by_function(jobs).set_index("Function")
    assert table.loc["Engineering", "Open_Now"] == 14 + 5 + 10
    assert table.loc["Sales & Partnerships", "Net_Change"] == -5


def test_roles_by_industry_counts_each_tag():
    jobs, companies = _history()
    table = mi.roles_by_industry(jobs, companies).set_index("Industry")
    assert table.loc["FinTech", "Open_Now"] == 14 + 15
    assert table.loc["AI", "Open_Now"] == 14 + 10
    assert table.loc["AI", "Previous_Open"] == 10


def test_open_roles_over_time():
    jobs, _ = _history()
    trend = mi.open_roles_over_time(jobs)
    assert list(trend["Open_Roles"]) == [35, 10, 44]


def test_single_snapshot_has_no_comparison():
    jobs, companies = _history()
    only_latest = jobs[jobs["Snapshot_Date"] == jobs["Snapshot_Date"].max()]
    assert mi.comparison_window(only_latest) is None
    assert mi.headline(only_latest)["new_roles"] is None
    assert mi.company_movers(only_latest, companies).empty
