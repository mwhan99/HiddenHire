"""Market-level views of the weekly job snapshots.

Everything here reads the same workbook as the job search and does not
change any scores. The functions return plain DataFrames so they can be
tested without Streamlit and shown in the app's Market Insights tab.
"""

import pandas as pd

from candidate_fit import contains_term
from hiring_momentum import (
    MIN_GAP_DAYS,
    choose_comparison_dates,
    size_adjusted,
)
from pipeline import FILE_PATH, is_active

# ==========================================
# JOB FUNCTIONS
# A title gets the first function whose keywords it contains as whole
# words. The order matters: "Data Scientist, Finance" is data, not
# finance, "Legal Operations" is legal, and "Revenue Operations Analyst"
# is operations, not sales.
# ==========================================

FUNCTION_RULES = [
    # Unambiguous titles first, so "Revenue Accountant" is finance and
    # "Recruiter, Financial Services" is recruiting.
    ("People & Recruiting", [
        "recruiter", "recruiting", "talent acquisition",
    ]),
    ("Finance, Legal & Compliance", [
        "accountant", "accounting", "controller", "payroll", "tax",
    ]),
    # Same grouping as the job search's operations role family.
    ("Operations & Strategy", [
        "revenue operations", "sales operations", "marketing operations",
        "business operations", "strategy and operations",
        "strategy & operations", "product operations",
    ]),
    ("Customer Success & Support", [
        "customer success", "customer support", "support", "implementation",
        "onboarding", "customer experience", "client services",
        "activation", "technical consultant", "customer operations",
        "client success", "professional services", "engagement manager",
    ]),
    ("Clinical & Care", [
        "clinical", "clinician", "physician", "nurse", "therapist",
        "psychiatrist", "provider network", "care coordinator", "pharmacist",
        "dietitian", "medical",
    ]),
    ("Sales & Partnerships", [
        "account executive", "sales", "sdr", "bdr", "business development",
        "partnerships", "partnership", "partner", "account manager",
        "solutions engineer", "sales engineer", "solutions consultant",
        "solutions architect", "gtm", "go-to-market", "revenue", "upsell",
        "representative", "deal desk",
    ]),
    ("Data & Analytics", [
        "data scientist", "data analyst", "data engineer", "analytics engineer",
        "business intelligence", "data science", "economist",
    ]),
    ("Finance, Legal & Compliance", [
        "finance", "financial", "accounting", "accountant", "controller",
        "fp&a", "tax", "payroll", "treasury", "legal", "counsel", "attorney",
        "compliance", "paralegal", "accounts payable", "accounts receivable",
        "payments", "procurement", "equity administration", "licensing",
        "credentialing",
    ]),
    ("Marketing & Creative", [
        "marketing", "brand", "content", "communications", "demand generation",
        "social media", "community", "creative", "copywriter", "events",
        "marketer",
    ]),
    ("Operations & Strategy", [
        "operations", "strategy", "strategic initiatives", "chief of staff",
        "program manager", "project manager", "business operations",
        "strategist", "program lead",
    ]),
    ("Design", [
        "designer", "design", "ux", "ui", "user research", "researcher, ux",
    ]),
    ("Engineering", [
        "engineer", "engineers", "engineering", "developer", "software",
        "sre", "devops", "architect", "machine learning", "technical staff",
        "scientist", "infrastructure",
    ]),
    ("Data & Analytics", [
        "analyst", "analytics", "insights",
    ]),
    ("Product", [
        "product", "products", "pm",
    ]),
    ("People & Recruiting", [
        "recruiter", "recruiting", "talent", "people", "hr", "human resources",
        "it administrator", "workplace", "office manager",
    ]),
]

OTHER_FUNCTION = "Other"


def classify_function(job_title):
    """Return the job function for a title, or "Other"."""
    if job_title is None or (isinstance(job_title, float) and pd.isna(job_title)):
        return OTHER_FUNCTION
    for function, keywords in FUNCTION_RULES:
        if any(contains_term(job_title, keyword) for keyword in keywords):
            return function
    return OTHER_FUNCTION


# ==========================================
# LOADING
# ==========================================

def load_history(file_path=FILE_PATH):
    """Return (jobs, companies) for active companies only.

    jobs has a normalized Snapshot_Date and a Job_Key column used to
    tell new and closed postings apart between snapshots.
    """
    companies = pd.read_excel(file_path, sheet_name="Companies")
    jobs = pd.read_excel(file_path, sheet_name="Job_Snapshots")
    return prepare_history(jobs, companies)


def prepare_history(jobs, companies):
    companies = companies.copy()
    companies["Company_ID"] = companies["Company_ID"].astype(str)
    active = companies[companies["Active"].apply(is_active)] if "Active" in companies else companies

    jobs = jobs.copy()
    jobs["Company_ID"] = jobs["Company_ID"].astype(str)
    jobs = jobs[jobs["Company_ID"].isin(set(active["Company_ID"]))]
    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"]).dt.normalize()
    jobs = jobs.dropna(subset=["Job_ID"])
    jobs["Job_Key"] = (
        jobs["Company_ID"] + "|" + jobs["Job_ID"].astype(str).str.strip()
    )
    jobs = jobs.drop_duplicates(subset=["Snapshot_Date", "Job_Key"])
    return jobs.reset_index(drop=True), active.reset_index(drop=True)


# ==========================================
# COMPARISON WINDOW
# ==========================================

def comparison_window(jobs):
    """(previous_date, current_date, gap_days) used for week-over-week views.

    Uses the same rule as Hiring Momentum: the snapshot closest to seven
    days before the latest one. Returns None when there is only one date.
    """
    dates = sorted(jobs["Snapshot_Date"].unique())
    if len(dates) < 2:
        return None
    previous, current = choose_comparison_dates(dates)
    return previous, current, (current - previous).days


def _snapshot(jobs, date):
    return jobs[jobs["Snapshot_Date"] == pd.Timestamp(date)]


# ==========================================
# HEADLINE NUMBERS
# ==========================================

def headline(jobs):
    """Open, new, and closed roles plus growing/slowing company counts."""
    window = comparison_window(jobs)
    latest_date = jobs["Snapshot_Date"].max()
    latest = _snapshot(jobs, latest_date)

    result = {
        "latest_date": latest_date,
        "companies": latest["Company_ID"].nunique(),
        "open_roles": len(latest),
        "previous_date": None,
        "gap_days": None,
        "previous_open_roles": None,
        "new_roles": None,
        "closed_roles": None,
        "companies_growing": None,
        "companies_slowing": None,
    }
    if window is None:
        return result

    previous_date, current_date, gap = window
    previous = _snapshot(jobs, previous_date)
    current = _snapshot(jobs, current_date)
    previous_keys = set(previous["Job_Key"])
    current_keys = set(current["Job_Key"])

    movers = company_movers(jobs)
    result.update(
        previous_date=previous_date,
        gap_days=gap,
        previous_open_roles=len(previous),
        new_roles=len(current_keys - previous_keys),
        closed_roles=len(previous_keys - current_keys),
        companies_growing=int((movers["Net_Change"] > 0).sum()),
        companies_slowing=int((movers["Net_Change"] < 0).sum()),
    )
    return result


# ==========================================
# COMPANY MOVERS
# ==========================================

def company_movers(jobs, companies=None):
    """One row per company with open roles before and now.

    Companies with no roles in the earlier snapshot (usually just added
    to the list) are left out, since every posting would look new.
    Growth_Rate is the net change divided by the earlier open roles,
    counted as at least 10, the same size adjustment Hiring Momentum uses.
    """
    window = comparison_window(jobs)
    columns = [
        "Company_ID", "Company", "Industry", "Previous_Open", "Open_Now",
        "Net_Change", "Change_Pct", "New_Roles", "Closed_Roles", "Growth_Rate",
    ]
    if window is None:
        return pd.DataFrame(columns=columns)

    previous_date, current_date, _ = window
    previous = _snapshot(jobs, previous_date)
    current = _snapshot(jobs, current_date)

    names = (
        jobs.sort_values("Snapshot_Date")
        .groupby("Company_ID")["Company_Name"].last()
    )
    ids = sorted(set(previous["Company_ID"]) | set(current["Company_ID"]))
    rows = []
    for company_id in ids:
        before = set(previous.loc[previous["Company_ID"] == company_id, "Job_Key"])
        now = set(current.loc[current["Company_ID"] == company_id, "Job_Key"])
        rows.append({
            "Company_ID": company_id,
            "Company": names.get(company_id, company_id),
            "Previous_Open": len(before),
            "Open_Now": len(now),
            "New_Roles": len(now - before),
            "Closed_Roles": len(before - now),
        })

    movers = pd.DataFrame(rows)
    movers = movers[movers["Previous_Open"] > 0].copy()
    movers["Net_Change"] = movers["Open_Now"] - movers["Previous_Open"]
    movers["Change_Pct"] = (
        movers["Net_Change"] / movers["Previous_Open"] * 100
    ).round(0)
    movers["Growth_Rate"] = size_adjusted(
        movers["Net_Change"], movers["Previous_Open"]
    )

    if companies is not None and "Industry" in companies:
        industry = companies.set_index(companies["Company_ID"].astype(str))["Industry"]
        movers["Industry"] = movers["Company_ID"].map(industry)
    else:
        movers["Industry"] = None

    return movers[columns].reset_index(drop=True)


def fastest_growing(movers, limit=8):
    growing = movers[movers["Net_Change"] > 0]
    return growing.sort_values(
        ["Growth_Rate", "Net_Change"], ascending=False
    ).head(limit).reset_index(drop=True)


def slowing_down(movers, limit=8):
    slowing = movers[movers["Net_Change"] < 0]
    return slowing.sort_values(
        ["Growth_Rate", "Net_Change"], ascending=True
    ).head(limit).reset_index(drop=True)


# ==========================================
# FUNCTION AND INDUSTRY BREAKDOWNS
# ==========================================

def _breakdown(previous_counts, current_counts, label):
    table = pd.DataFrame({
        "Open_Now": current_counts,
        "Previous_Open": previous_counts,
    }).fillna(0).astype(int)
    table["Net_Change"] = table["Open_Now"] - table["Previous_Open"]
    table.index.name = label
    return (
        table.reset_index()
        .sort_values(["Open_Now", label], ascending=[False, True])
        .reset_index(drop=True)
    )


def roles_by_function(jobs):
    """Open roles per job function now and in the comparison snapshot."""
    window = comparison_window(jobs)
    latest_date = jobs["Snapshot_Date"].max()
    current = _snapshot(jobs, window[1] if window else latest_date)
    current_counts = current["Job_Title"].map(classify_function).value_counts()

    if window is None:
        previous_counts = pd.Series(dtype=int)
    else:
        previous = _snapshot(jobs, window[0])
        previous_counts = previous["Job_Title"].map(classify_function).value_counts()

    table = _breakdown(previous_counts, current_counts, "Function")
    # Keep "Other" at the bottom regardless of size.
    other = table["Function"] == OTHER_FUNCTION
    return pd.concat([table[~other], table[other]]).reset_index(drop=True)


def industry_tags(industry):
    """Split a label like "AI / FinTech / SaaS" into its tags."""
    if industry is None or (isinstance(industry, float) and pd.isna(industry)):
        return []
    return [tag.strip() for tag in str(industry).split("/") if tag.strip()]


def roles_by_industry(jobs, companies, limit=10):
    """Open roles per industry tag. A company can carry several tags,
    so its roles count toward each of them."""
    tags = {
        str(row.Company_ID): industry_tags(row.Industry)
        for row in companies.itertuples()
    }

    def counts(snapshot):
        per_company = snapshot.groupby("Company_ID").size()
        totals = {}
        for company_id, count in per_company.items():
            for tag in tags.get(str(company_id), []):
                totals[tag] = totals.get(tag, 0) + int(count)
        return pd.Series(totals, dtype=int)

    window = comparison_window(jobs)
    latest_date = jobs["Snapshot_Date"].max()
    current = counts(_snapshot(jobs, window[1] if window else latest_date))
    previous = counts(_snapshot(jobs, window[0])) if window else pd.Series(dtype=int)

    return _breakdown(previous, current, "Industry").head(limit)


# ==========================================
# TREND
# ==========================================

def open_roles_over_time(jobs):
    """Total open roles and companies with openings at each snapshot."""
    trend = (
        jobs.groupby("Snapshot_Date")
        .agg(Open_Roles=("Job_Key", "nunique"), Companies=("Company_ID", "nunique"))
        .reset_index()
        .sort_values("Snapshot_Date")
    )
    return trend.reset_index(drop=True)


__all__ = [
    "MIN_GAP_DAYS",
    "classify_function",
    "company_movers",
    "comparison_window",
    "fastest_growing",
    "headline",
    "industry_tags",
    "load_history",
    "open_roles_over_time",
    "prepare_history",
    "roles_by_function",
    "roles_by_industry",
    "slowing_down",
]
