import re
import sys
from datetime import date
from urllib.parse import urlparse

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


def resolved_identifier(company):
    """Use ATS_Identifier, or the Ashby board slug from Careers_URL."""
    identifier = company["ATS_Identifier"]
    if pd.notna(identifier) and str(identifier).strip():
        return str(identifier).strip()

    url = company["Careers_URL"]
    if pd.isna(url):
        return None

    parsed = urlparse(str(url).strip())
    if parsed.netloc.lower() != "jobs.ashbyhq.com":
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


def is_active(value):
    """Blank counts as active. False, 0, "no", or "inactive" does not."""
    if value is None or pd.isna(value):
        return True
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "no", "n", "0", "inactive"}
    return bool(value)


# 1. Read Companies sheet
companies = pd.read_excel(
    FILE_PATH,
    sheet_name="Companies"
)

# 2. Keep only active Ashby companies
ashby_companies = companies[
    (companies["ATS"] == "Ashby")
    & companies["Active"].apply(is_active)
]

snapshot_rows = []
fetch_errors = []

# 3. Visit each Ashby company
for _, company in ashby_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = str(company["Company_Name"]).strip()
    identifier = resolved_identifier(company)

    # Skip companies without an identifier
    if not identifier:
        print(f"Skipping {company_name}: no ATS identifier")
        continue

    url = f"https://api.ashbyhq.com/posting-api/job-board/{identifier}"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        jobs = response.json().get("jobs") or []

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
                "Job_Description": excel_description(job.get("descriptionPlain")),
                "ATS": "Ashby"
            })

    except Exception as e:
        fetch_errors.append(f"ERROR - {company_name}: {e}")

if fetch_errors:
    fail_without_saving(fetch_errors)

# 5. Combine everything into one dataframe
snapshot_df = pd.DataFrame(snapshot_rows)

print("\nCollection complete!")
print("Total Ashby jobs collected:", len(snapshot_df))

if not snapshot_df.empty:
    print(
        snapshot_df[
            ["Company_ID", "Company_Name", "Job_Title", "Location"]
        ].head(20)
    )

# 6. Save snapshots while preserving historical data
#    and today's Greenhouse and Lever rows.

try:
    existing_snapshots = pd.read_excel(
        FILE_PATH,
        sheet_name="Job_Snapshots"
    )
except Exception:
    existing_snapshots = pd.DataFrame()

today = pd.Timestamp(date.today()).normalize()

# Convert existing Snapshot_Date to datetime
if not existing_snapshots.empty:
    existing_snapshots["Snapshot_Date"] = pd.to_datetime(
        existing_snapshots["Snapshot_Date"]
    )

    # Remove today's old Ashby snapshot if the script is run again today.
    # Keep today's other ATS rows and every previous date.
    existing_snapshots = existing_snapshots[
        ~(
            (existing_snapshots["Snapshot_Date"].dt.normalize() == today)
            & (existing_snapshots["ATS"] == "Ashby")
        )
    ]

# Combine historical snapshots + today's new snapshot
all_snapshots = pd.concat(
    [existing_snapshots, snapshot_df],
    ignore_index=True
)

# Write everything back to Excel
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

print("\nHistorical snapshots saved successfully!")
print("Today's jobs:", len(snapshot_df))
print("Total snapshot rows:", len(all_snapshots))
