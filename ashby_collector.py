import pandas as pd
import requests
from datetime import date

# 1. Read Companies sheet
companies = pd.read_excel(
    "HiddenHire_Data.xlsx",
    sheet_name="Companies"
)

# 2. Keep only Ashby companies
ashby_companies = companies[
    companies["ATS"] == "Ashby"
]

snapshot_rows = []

# 3. Visit each Ashby company
for _, company in ashby_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = company["Company_Name"]
    identifier = company["ATS_Identifier"]

    # Skip companies without an identifier
    if pd.isna(identifier):
        print(f"Skipping {company_name}: no ATS identifier")
        continue

    url = f"https://api.ashbyhq.com/posting-api/job-board/{identifier}"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        jobs = response.json().get("jobs", [])

        print(f"{company_name}: {len(jobs)} jobs")

        # 4. Convert each job into our snapshot format
        for job in jobs:
            snapshot_rows.append({
                "Snapshot_Date": date.today(),
                "Company_ID": company_id,
                "Company_Name": company_name,
                "Job_ID": job.get("id"),
                "Job_Title": job.get("title"),
                "Department": job.get("department"),
                "Location": job.get("location"),
                "Employment_Type": job.get("employmentType"),
                "Date_Posted": job.get("publishedAt"),
                "Job_URL": job.get("jobUrl"),
                "Job_Description": job.get("descriptionPlain"),
                "ATS": "Ashby"
            })

    except Exception as e:
        print(f"ERROR - {company_name}: {e}")

# 5. Combine everything into one dataframe
snapshot_df = pd.DataFrame(snapshot_rows)

print("\nCollection complete!")
print("Total Ashby jobs collected:", len(snapshot_df))

print(
    snapshot_df[
        ["Company_ID", "Company_Name", "Job_Title", "Location"]
    ].head(20)
)
# 6. Save snapshots while preserving historical data

try:
    existing_snapshots = pd.read_excel(
        "HiddenHire_Data.xlsx",
        sheet_name="Job_Snapshots"
    )
except Exception:
    existing_snapshots = pd.DataFrame()

today = pd.Timestamp(date.today())

# Convert existing Snapshot_Date to datetime
if not existing_snapshots.empty:
    existing_snapshots["Snapshot_Date"] = pd.to_datetime(
        existing_snapshots["Snapshot_Date"]
    )

    # Remove today's old snapshot if the script is run again today
    existing_snapshots = existing_snapshots[
        existing_snapshots["Snapshot_Date"] != today
    ]

# Combine historical snapshots + today's new snapshot
all_snapshots = pd.concat(
    [existing_snapshots, snapshot_df],
    ignore_index=True
)

# Write everything back to Excel
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

print("\nHistorical snapshots saved successfully!")
print("Today's jobs:", len(snapshot_df))
print("Total snapshot rows:", len(all_snapshots))