import html
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


HTML_TAG = re.compile(r"<[^>]+>")
BLOCK_TAG = re.compile(r"</?(p|div|br|li|ul|ol|h[1-6])[^>]*>", re.IGNORECASE)


def html_to_text(content):
    """Turn a Lever HTML fragment (<li>...</li>) into plain text."""
    if not content:
        return ""
    text = BLOCK_TAG.sub(" ", str(content))
    text = HTML_TAG.sub("", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def full_description(job):
    """Combine every text section of a Lever posting.

    descriptionPlain is only the opening section. The responsibilities
    and requirements bullets are in "lists", and closing notes are in
    additionalPlain, so all three are joined for skill matching.
    """
    parts = [job.get("descriptionPlain") or ""]

    for section in job.get("lists") or []:
        heading = (section.get("text") or "").strip()
        bullets = html_to_text(section.get("content"))
        if heading or bullets:
            parts.append(f"{heading}: {bullets}" if heading else bullets)

    parts.append(job.get("additionalPlain") or "")

    text = "\n".join(part.strip() for part in parts if part and part.strip())
    return text or None


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

# 2. Keep only active Lever companies
lever_companies = companies[
    (companies["ATS"] == "Lever")
    & companies["Active"].apply(is_active)
]

snapshot_rows = []
fetch_errors = []

# 3. Collect jobs from every Lever company
for _, company in lever_companies.iterrows():

    company_id = company["Company_ID"]
    company_name = str(company["Company_Name"]).strip()
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
                    full_description(job)
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
