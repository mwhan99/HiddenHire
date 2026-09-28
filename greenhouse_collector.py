import pandas as pd
import requests
from datetime import date

# 1. Read Companies sheet
companies = pd.read_excel(
    "HiddenHire_Data.xlsx",
    sheet_name="Companies"
)

# 2. Keep only Greenhouse companies
greenhouse_companies = companies[
    companies["ATS"] == "Greenhouse"
]

snapshot_rows = []

# 3. Visit each Greenhouse company
for _, company in greenhouse_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = company["Company_Name"]
    identifier = company["ATS_Identifier"]

    if pd.isna(identifier):
        print(f"Skipping {company_name}: no ATS identifier")
        continue

    url = f"https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        jobs = response.json().get("jobs", [])

        print(f"{company_name}: {len(jobs)} jobs")

        for job in jobs:
            snapshot_rows.append({
                "Snapshot_Date": date.today(),
                "Company_ID": company_id,
                "Company_Name": company_name,
                "Job_ID": job.get("id"),
                "Job_Title": job.get("title"),
                "Department": None,
                "Location": job.get("location", {}).get("name"),
                "Employment_Type": None,
                "Date_Posted": job.get("first_published"),
                "Job_URL": job.get("absolute_url"),
                "Job_Description": None,
                "ATS": "Greenhouse"
            })

    except Exception as e:
        print(f"ERROR - {company_name}: {e}")

# 4. Combine all Greenhouse jobs
snapshot_df = pd.DataFrame(snapshot_rows)

print("\nGreenhouse collection complete!")
print("Total Greenhouse jobs collected:", len(snapshot_df))

# 5. Save Greenhouse jobs into Job_Snapshots
# while preserving Ashby and historical snapshots

existing_snapshots = pd.read_excel(
    "HiddenHire_Data.xlsx",
    sheet_name="Job_Snapshots"
)

today = pd.Timestamp(date.today())

# Make sure Snapshot_Date is datetime
existing_snapshots["Snapshot_Date"] = pd.to_datetime(
    existing_snapshots["Snapshot_Date"]
)

# Remove only today's OLD Greenhouse snapshot
# Keep today's Ashby data and all previous dates
existing_snapshots = existing_snapshots[
    ~(
        (existing_snapshots["Snapshot_Date"] == today)
        & (existing_snapshots["ATS"] == "Greenhouse")
    )
]

# Add today's fresh Greenhouse snapshot
all_snapshots = pd.concat(
    [existing_snapshots, snapshot_df],
    ignore_index=True
)

# Save back to Excel
with pd.ExcelWriter(
    "HiddenHire_Data.xlsx",
    engine="openpyxl",
    mode="a",
    if_sheet_exists="replace"
) as writer:
    all_snapshots.to_excel(
        writer,
        sheet_name="Job_Snapshots",
        index=False
    )

print("\nGreenhouse snapshot saved successfully!")
print("Today's Greenhouse jobs:", len(snapshot_df))
print("Total Job_Snapshots rows:", len(all_snapshots))