import re
import sys
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import requests

FILE_PATH = "HiddenHire_Data.xlsx"
EXCEL_CELL_LIMIT = 32767
ILLEGAL_EXCEL_CHARS = re.compile("[\000-\010]|[\013-\014]|[\016-\037]")
GREENHOUSE_HOSTS = {
    "job-boards.greenhouse.io",
    "boards.greenhouse.io",
}


def excel_description(value):
    """Return a Job_Description that Excel can store."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = ILLEGAL_EXCEL_CHARS.sub("", str(value))
    return text[:EXCEL_CELL_LIMIT]


def resolved_identifier(company):
    """Use ATS_Identifier, or the Greenhouse board slug from Careers_URL."""
    identifier = company["ATS_Identifier"]
    if pd.notna(identifier) and str(identifier).strip():
        return str(identifier).strip()

    url = company["Careers_URL"]
    if pd.isna(url):
        return None

    parsed = urlparse(str(url).strip())
    if parsed.netloc.lower() not in GREENHOUSE_HOSTS:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None
    return parts[0]


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

# 2. Keep only Greenhouse companies
greenhouse_companies = companies[
    companies["ATS"] == "Greenhouse"
]

snapshot_rows = []
fetch_errors = []

# 3. Visit each Greenhouse company
for _, company in greenhouse_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = company["Company_Name"]
    identifier = resolved_identifier(company)

    if not identifier:
        print(f"Skipping {company_name}: no ATS identifier")
        continue

    url = f"https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        jobs = response.json().get("jobs") or []

        print(f"{company_name}: {len(jobs)} jobs")

        for job in jobs:
            location = job.get("location")
            location_name = (
                location.get("name") if isinstance(location, dict) else None
            )
            snapshot_rows.append({
                "Snapshot_Date": date.today(),
                "Company_ID": company_id,
                "Company_Name": company_name,
                "Job_ID": job.get("id"),
                "Job_Title": job.get("title"),
                "Department": None,
                "Location": location_name,
                "Employment_Type": None,
                "Date_Posted": job.get("first_published"),
                "Job_URL": job.get("absolute_url"),
                "Job_Description": excel_description(None),
                "ATS": "Greenhouse"
            })

    except Exception as e:
        fetch_errors.append(f"ERROR - {company_name}: {e}")

if fetch_errors:
    fail_without_saving(fetch_errors)

# 4. Combine all Greenhouse jobs
snapshot_df = pd.DataFrame(snapshot_rows)

print("\nGreenhouse collection complete!")
print("Total Greenhouse jobs collected:", len(snapshot_df))

# 5. Save Greenhouse jobs into Job_Snapshots
# while preserving other ATS rows and historical snapshots

existing_snapshots = pd.read_excel(
    FILE_PATH,
    sheet_name="Job_Snapshots"
)

today = pd.Timestamp(date.today()).normalize()

# Make sure Snapshot_Date is datetime
existing_snapshots["Snapshot_Date"] = pd.to_datetime(
    existing_snapshots["Snapshot_Date"]
)

# Remove only today's old Greenhouse snapshot.
# Keep today's other ATS rows and all previous dates.
existing_snapshots = existing_snapshots[
    ~(
        (existing_snapshots["Snapshot_Date"].dt.normalize() == today)
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

print("\nGreenhouse snapshot saved successfully!")
print("Today's Greenhouse jobs:", len(snapshot_df))
print("Total Job_Snapshots rows:", len(all_snapshots))
