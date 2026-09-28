import re
import sys
from datetime import date

import pandas as pd
import requests

FILE_PATH = "HiddenHire_Data.xlsx"
EXCEL_CELL_LIMIT = 32767
ILLEGAL_EXCEL_CHARS = re.compile("[\000-\010]|[\013-\014]|[\016-\037]")


def excel_description(value):
    """Return a Job_Description that Excel can store."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = ILLEGAL_EXCEL_CHARS.sub("", str(value))
    return text[:EXCEL_CELL_LIMIT]


def fail_without_saving(messages):
    for message in messages:
        print(message, file=sys.stderr)
    print("Job_Snapshots was not changed.", file=sys.stderr)
    sys.exit(1)


# 1. Read Companies sheet
companies = pd.read_excel(
    FILE_PATH,
    sheet_name="Companies"
)

# 2. Keep only Lever companies
lever_companies = companies[
    companies["ATS"] == "Lever"
]

snapshot_rows = []
fetch_errors = []

# 3. Collect jobs from every Lever company
for _, company in lever_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = company["Company_Name"]
    identifier = company["ATS_Identifier"]

    if pd.isna(identifier) or not str(identifier).strip():
        print(f"Skipping {company_name}: no ATS identifier")
        continue

    identifier = str(identifier).strip()
    url = f"https://api.lever.co/v0/postings/{identifier}?mode=json"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        jobs = response.json()
        if not isinstance(jobs, list):
            raise ValueError("Lever response did not contain a job list")

        print(f"{company_name}: {len(jobs)} jobs")

        for job in jobs:
            categories = job.get("categories") or {}

            snapshot_rows.append({
                "Snapshot_Date": date.today(),
                "Company_ID": company_id,
                "Company_Name": company_name,
                "Job_ID": job.get("id"),
                "Job_Title": job.get("text"),
                "Department": categories.get("team"),
                "Location": categories.get("location"),
                "Employment_Type": categories.get("commitment"),
                "Date_Posted": pd.to_datetime(
                    job.get("createdAt"),
                    unit="ms",
                    errors="coerce"
                ),
                "Job_URL": job.get("hostedUrl"),
                "Job_Description": excel_description(
                    job.get("descriptionPlain")
                ),
                "ATS": "Lever"
            })

    except Exception as e:
        fetch_errors.append(f"ERROR - {company_name}: {e}")

if fetch_errors:
    fail_without_saving(fetch_errors)

# 4. Combine all Lever jobs
snapshot_df = pd.DataFrame(snapshot_rows)

print("\nLever collection complete!")
print("Total Lever jobs collected:", len(snapshot_df))

# 5. Save Lever jobs into Job_Snapshots
# while preserving other ATS and historical snapshots

existing_snapshots = pd.read_excel(
    FILE_PATH,
    sheet_name="Job_Snapshots"
)

today = pd.Timestamp(date.today()).normalize()

existing_snapshots["Snapshot_Date"] = pd.to_datetime(
    existing_snapshots["Snapshot_Date"]
)

# Remove only today's old Lever snapshot
existing_snapshots = existing_snapshots[
    ~(
        (existing_snapshots["Snapshot_Date"].dt.normalize() == today)
        & (existing_snapshots["ATS"] == "Lever")
    )
]

# Add today's fresh Lever snapshot
all_snapshots = pd.concat(
    [existing_snapshots, snapshot_df],
    ignore_index=True
)

with pd.ExcelWriter(
    FILE_PATH,
    engine="openpyxl",
    mode="a",
    if_sheet_exists="replace"
) as writer:
    all_snapshots.to_excel(
        writer,
        sheet_name="Job_Snapshots",
        index=False
    )

print("\nLever snapshot saved successfully!")
print("Today's Lever jobs:", len(snapshot_df))
print("Total Job_Snapshots rows:", len(all_snapshots))
