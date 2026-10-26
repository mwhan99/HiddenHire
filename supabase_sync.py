"""Copy HiddenHire_Data.xlsx into the Supabase tables in supabase/schema.sql.

The workbook stays the source of truth. This script only reads it and
writes to Supabase, so it can be run as often as needed: every row is
"upserted" (added, or updated if it already exists).

Usage:
    python supabase_sync.py --dry-run   # build everything, send nothing
    python supabase_sync.py             # send to Supabase

Sending needs two settings, read from the environment or from a .env
file next to this script (.env is git-ignored):
    SUPABASE_URL=https://<project>.supabase.co
    SUPABASE_SECRET_KEY=<the project's secret / service_role key>

Only the standard library, pandas, and requests are used, so nothing
new is added to requirements.txt (which the Streamlit site installs).
"""

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timezone

import pandas as pd
import requests

import market_insights
from candidate_fit import ROLE_FAMILIES, calculate_family_match, classify_seniority
from pipeline import FILE_PATH, is_active

BATCH_SIZE = 500
TIMEOUT = 60


# ==========================================
# SMALL CONVERSIONS
# ==========================================

def clean(value):
    """Turn pandas/numpy values into plain JSON values (NaN -> None)."""
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if hasattr(value, "item"):          # numpy int64, float64, bool_
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def text(value):
    """A stripped string, or None for blanks."""
    value = clean(value)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def job_id_text(value):
    """Job IDs as text. Greenhouse IDs are numbers; 6598283003.0 must
    become "6598283003", the same key the Python scoring uses."""
    value = clean(value)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return text(value)


def day(value):
    """A date as "YYYY-MM-DD", or None."""
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def timestamp(value):
    """Date_Posted comes in several formats (Ashby and Greenhouse send
    ISO text, Lever is converted from milliseconds). Returns UTC ISO
    text, or None when it cannot be read."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    return None if pd.isna(parsed) else parsed.isoformat()


def records(frame):
    """A DataFrame as a list of plain dicts with snake_case keys."""
    return [
        {column.lower(): clean(value) for column, value in row.items()}
        for row in frame.to_dict("records")
    ]


# ==========================================
# ROWS FOR EACH TABLE
# ==========================================

def role_families(job_title):
    """Role families the title belongs to, using the same rules
    (including exclusions) as Candidate Fit."""
    return [
        family for family in ROLE_FAMILIES
        if calculate_family_match(job_title, [family]) > 0
    ]


def company_rows(companies):
    return [
        {
            "company_id": text(row["Company_ID"]),
            "company_name": text(row["Company_Name"]),
            "industry": text(row.get("Industry")),
            "location": text(row.get("Location")),
            "company_size": text(row.get("Company_Size")),
            "company_stage": text(row.get("Company_Stage")),
            "company_website": text(row.get("Company_Website")),
            "careers_url": text(row.get("Careers_URL")),
            "ats": text(row.get("ATS")),
            "ats_identifier": text(row.get("ATS_Identifier")),
            "source": text(row.get("Source")),
            "date_added": day(row.get("Date_Added")),
            "active": is_active(row.get("Active")),
        }
        for row in companies.to_dict("records")
    ]


def job_snapshot_rows(jobs):
    """Every snapshot row, without the description, plus the three
    labels the website uses (role families, seniority, job function)."""
    rows = []
    for row in jobs.to_dict("records"):
        title = text(row.get("Job_Title"))
        rows.append({
            "snapshot_date": day(row["Snapshot_Date"]),
            "ats": text(row["ATS"]),
            "company_id": text(row["Company_ID"]),
            "job_id": job_id_text(row["Job_ID"]),
            "company_name": text(row.get("Company_Name")),
            "job_title": title,
            "department": text(row.get("Department")),
            "location": text(row.get("Location")),
            "employment_type": text(row.get("Employment_Type")),
            "date_posted": timestamp(row.get("Date_Posted")),
            "job_url": text(row.get("Job_URL")),
            "role_families": role_families(title),
            "seniority": classify_seniority(title),
            "job_function": market_insights.classify_function(title),
        })
    return rows


def description_rows(jobs):
    """One description per job: the text from the latest snapshot that
    had the job, with that snapshot's date as last_seen."""
    latest = (
        jobs.assign(_date=pd.to_datetime(jobs["Snapshot_Date"]))
        .sort_values("_date")
        .assign(_key=lambda frame: frame["Job_ID"].map(job_id_text))
        .drop_duplicates(subset=["Company_ID", "_key"], keep="last")
    )
    return [
        {
            "company_id": text(row["Company_ID"]),
            "job_id": row["_key"],
            "description": text(row.get("Job_Description")),
            "last_seen": day(row["_date"]),
        }
        for row in latest.to_dict("records")
    ]


def momentum_rows(history, companies, snapshot_date):
    """The Company Momentum leaderboard as it looked on snapshot_date.
    history is market_insights.prepare_history output for every date."""
    jobs = history[history["Snapshot_Date"] <= pd.Timestamp(snapshot_date)]
    board = market_insights.company_momentum(jobs, companies)
    rows = []
    for rank, row in enumerate(board.to_dict("records"), start=1):
        company_id = row["Company_ID"]
        rows.append({
            "snapshot_date": day(snapshot_date),
            "company_id": company_id,
            "company_name": text(row["Company"]),
            "open_now": int(row["Open_Now"]),
            "net_change": clean(row["Net_Change"]),
            "new_roles": clean(row["New_Roles"]),
            "closed_roles": clean(row["Closed_Roles"]),
            "growth_rate": clean(row["Growth_Rate"]),
            "momentum": row["Momentum"],
            "rank": rank,
            "trend": [int(value) for value in row["Trend"]],
            "functions": records(
                market_insights.company_functions(jobs, company_id)
            ),
            "new_postings": records(
                market_insights.company_new_roles(jobs, company_id)
            ),
        })
    # Whole numbers come back from pandas as floats (2.0); store ints.
    for row in rows:
        for column in ["net_change", "new_roles", "closed_roles"]:
            if row[column] is not None:
                row[column] = int(row[column])
    return rows


def summary_row(history, companies, curated_count, snapshot_date):
    """Stats bar, Market Insights, and coverage numbers for one date."""
    jobs = history[history["Snapshot_Date"] <= pd.Timestamp(snapshot_date)]
    movers = market_insights.company_movers(jobs, companies)
    return {
        "snapshot_date": day(snapshot_date),
        "headline": clean(market_insights.headline(jobs)),
        "growing": records(market_insights.fastest_growing(movers)),
        "slowing": records(market_insights.slowing_down(movers)),
        "functions": records(market_insights.roles_by_function(jobs)),
        "industries": records(market_insights.roles_by_industry(jobs, companies)),
        "trend": records(market_insights.open_roles_over_time(jobs)),
        "coverage": {
            "curated": int(curated_count),
            "active": int(len(companies)),
            "by_ats": clean(companies["ATS"].value_counts().to_dict()),
        },
    }


def build_tables(companies, jobs):
    """Everything to send, keyed by table name, in the order to send it
    (companies first, because the other tables point at them)."""
    history, active = market_insights.prepare_history(jobs, companies)
    dates = sorted(history["Snapshot_Date"].unique())
    tables = {
        "companies": company_rows(companies),
        "job_snapshots": job_snapshot_rows(jobs),
        "job_descriptions": description_rows(jobs),
        "company_momentum": [
            row for snapshot_date in dates
            for row in momentum_rows(history, active, snapshot_date)
        ],
        "market_summary": [
            summary_row(history, active, len(companies), snapshot_date)
            for snapshot_date in dates
        ],
    }
    # The schema's default only fills updated_at when a row is first
    # added, so send it on every sync to record when it was last saved.
    synced_at = datetime.now(timezone.utc).isoformat()
    for table in ["companies", "market_summary"]:
        for row in tables[table]:
            row["updated_at"] = synced_at
    return tables


# Columns that identify a row, matching each table's primary key.
PRIMARY_KEYS = {
    "companies": ["company_id"],
    "job_snapshots": ["snapshot_date", "ats", "company_id", "job_id"],
    "job_descriptions": ["company_id", "job_id"],
    "company_momentum": ["snapshot_date", "company_id"],
    "market_summary": ["snapshot_date"],
}

# Tables where a row can disappear from the workbook (a job removed by a
# same-day re-run, a company that left the board). Rows Supabase has for
# a synced date but the workbook does not are deleted.
PRUNE_BY_DATE = ["job_snapshots", "company_momentum"]


# ==========================================
# SUPABASE
# ==========================================

def read_env_file(path):
    """KEY=VALUE lines from a .env file. Missing file -> {}."""
    values = {}
    if not os.path.exists(path):
        return values
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def base_url(url):
    """The project address without a trailing /rest/v1/, so the URL can
    be pasted exactly as the dashboard's Data API page shows it."""
    url = url.strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    return url


def settings():
    """(url, key) from the environment, falling back to .env."""
    env_file = read_env_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    url = os.environ.get("SUPABASE_URL") or env_file.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY") or env_file.get("SUPABASE_SECRET_KEY")
    if not url or not key:
        sys.exit(
            "SUPABASE_URL and SUPABASE_SECRET_KEY are not set. Add them to "
            ".env (see the top of supabase_sync.py) or use --dry-run."
        )
    return base_url(url), key.strip()


def headers(key):
    """Request headers for a Supabase key.

    New-style secret keys (sb_secret_...) go only in the apikey header.
    Older service_role keys are JWTs and also go in Authorization.
    """
    result = {"apikey": key, "Content-Type": "application/json"}
    if not key.startswith("sb_"):
        result["Authorization"] = f"Bearer {key}"
    return result


def batches(rows, size=BATCH_SIZE):
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def check(response, action):
    if response.status_code >= 300:
        sys.exit(f"{action} failed ({response.status_code}): {response.text[:500]}")


def upsert(session, url, table, rows):
    endpoint = f"{url}/rest/v1/{table}"
    params = {"on_conflict": ",".join(PRIMARY_KEYS[table])}
    # Descriptions are long, so send fewer per request.
    size = 100 if table == "job_descriptions" else BATCH_SIZE
    for batch in batches(rows, size):
        response = session.post(
            endpoint,
            params=params,
            data=json.dumps(batch),
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            timeout=TIMEOUT,
        )
        check(response, f"Saving {table}")


def remote_keys(session, url, table, snapshot_date):
    columns = PRIMARY_KEYS[table]
    keys, start = set(), 0
    while True:
        response = session.get(
            f"{url}/rest/v1/{table}",
            params={"select": ",".join(columns), "snapshot_date": f"eq.{snapshot_date}"},
            headers={"Range": f"{start}-{start + 999}"},
            timeout=TIMEOUT,
        )
        check(response, f"Reading {table}")
        page = response.json()
        keys |= {tuple(str(row[column]) for column in columns) for row in page}
        if len(page) < 1000:
            return keys
        start += 1000


def prune(session, url, table, rows):
    """Delete rows Supabase has for a synced date that the workbook no
    longer has. Returns how many were deleted."""
    columns = PRIMARY_KEYS[table]
    local = {tuple(str(row[column]) for column in columns) for row in rows}
    deleted = 0
    for snapshot_date in sorted({row["snapshot_date"] for row in rows}):
        for key in remote_keys(session, url, table, snapshot_date) - local:
            response = session.delete(
                f"{url}/rest/v1/{table}",
                params={column: f"eq.{value}" for column, value in zip(columns, key)},
                timeout=TIMEOUT,
            )
            check(response, f"Deleting an old {table} row")
            deleted += 1
    return deleted


def count_rows(session, url, table, filters=None):
    response = session.get(
        f"{url}/rest/v1/{table}",
        params={"select": PRIMARY_KEYS[table][0], **(filters or {})},
        headers={"Prefer": "count=exact", "Range": "0-0"},
        timeout=TIMEOUT,
    )
    check(response, f"Counting {table}")
    return int(response.headers["Content-Range"].split("/")[-1])


def send(tables, url, key):
    session = requests.Session()
    session.headers.update(headers(key))

    for table, rows in tables.items():
        upsert(session, url, table, rows)
        print(f"Saved {len(rows):,} rows to {table}.")
        if table in PRUNE_BY_DATE:
            deleted = prune(session, url, table, rows)
            if deleted:
                print(f"  Removed {deleted:,} old rows from {table}.")

    # Compare what Supabase now holds with what was sent.
    problems = []
    for table, rows in tables.items():
        if table in PRUNE_BY_DATE:
            continue
        remote = count_rows(session, url, table)
        if remote < len(rows):
            problems.append(f"{table}: sent {len(rows):,}, Supabase has {remote:,}")
    latest = max(row["snapshot_date"] for row in tables["job_snapshots"])
    expected = sum(row["snapshot_date"] == latest for row in tables["job_snapshots"])
    remote = count_rows(session, url, "job_snapshots", {"snapshot_date": f"eq.{latest}"})
    print(f"Check: {latest} has {remote:,} jobs in Supabase and {expected:,} in the workbook.")
    if remote != expected:
        problems.append(f"job_snapshots on {latest}: expected {expected:,}, found {remote:,}")
    if problems:
        sys.exit("Sync finished with mismatches:\n" + "\n".join(problems))
    print("Sync complete. Supabase matches the workbook.")


# ==========================================
# MAIN
# ==========================================

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Build every row and print counts without sending anything.")
    parser.add_argument("--file", default=FILE_PATH, help="Workbook to read.")
    args = parser.parse_args(argv)

    companies = pd.read_excel(args.file, sheet_name="Companies")
    jobs = pd.read_excel(args.file, sheet_name="Job_Snapshots")
    tables = build_tables(companies, jobs)

    for table, rows in tables.items():
        print(f"{table}: {len(rows):,} rows")
    if args.dry_run:
        print("Dry run: nothing was sent.")
        return

    url, key = settings()
    send(tables, url, key)


if __name__ == "__main__":
    main()
