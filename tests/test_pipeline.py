import pandas as pd

import pipeline


def test_is_active():
    assert pipeline.is_active(None)
    assert pipeline.is_active(float("nan"))
    assert pipeline.is_active(True)
    assert pipeline.is_active(1)
    assert not pipeline.is_active(False)
    assert not pipeline.is_active(0)
    assert not pipeline.is_active("No")


def _workbook(path):
    companies = pd.DataFrame(
        {
            "Company_ID": ["C1", "C2"],
            "Company_Name": ["Active Co", "Inactive Co"],
            "Industry": ["FinTech", "FinTech"],
            "Active": [True, False],
        }
    )
    rows = []
    # Inactive Co had jobs last week and was not collected this week.
    for date, company, name, job_id, title in [
        ("2026-09-21", "C1", "Active Co", "1", "Business Analyst"),
        ("2026-09-21", "C2", "Inactive Co", "2", "Business Analyst"),
        ("2026-09-21", "C2", "Inactive Co", "3", "Data Analyst"),
        ("2026-09-28", "C1", "Active Co", "1", "Business Analyst"),
        ("2026-09-28", "C1", "Active Co", "4", "Data Analyst"),
    ]:
        rows.append(
            {
                "Snapshot_Date": date,
                "Company_ID": company,
                "Company_Name": name,
                "Job_ID": job_id,
                "Job_Title": title,
                "Location": "New York, NY",
                "Job_URL": "https://example.com",
                "Job_Description": "SQL",
            }
        )
    with pd.ExcelWriter(path) as writer:
        companies.to_excel(writer, sheet_name="Companies", index=False)
        pd.DataFrame(rows).to_excel(writer, sheet_name="Job_Snapshots", index=False)


def test_inactive_companies_are_left_out(tmp_path):
    path = tmp_path / "data.xlsx"
    _workbook(path)

    results = pipeline.rank_hidden_opportunities(
        ["business analyst"], ["SQL"], ["fintech"], "New York", file_path=path
    )

    assert set(results["Company_Name"]) == {"Active Co"}
    # Only Active Co is scored, so it grew and scores above neutral.
    assert (results["Hiring_Momentum_Score"] > 50).all()
