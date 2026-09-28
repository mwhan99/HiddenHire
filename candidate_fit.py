import pandas as pd

FILE_PATH = "HiddenHire_Data.xlsx"

# ==========================================
# TEST USER PROFILE
# ==========================================

user_profile = {
    "target_roles": [
        "business analyst",
        "strategy analyst",
        "operations analyst"
    ],

    "skills": [
        "sql",
        "excel",
        "tableau",
        "python"
    ],

    "industries": [
        "fintech",
        "ai",
        "enterprise software"
    ],

 "experience_level": [
        "intern",
        "entry level",
        "associate"
    ],

    "location": "New York"
}

# ==========================================
# ROLE FAMILY MAPPING
# ==========================================

ROLE_FAMILIES = {
    "business_analytics": [
        "business analyst",
        "data analyst",
        "business intelligence",
        "analytics analyst",
        "insights analyst"
    ],

    "strategy": [
        "strategy analyst",
        "strategy associate",
        "strategic planning",
        "corporate strategy",
        "business strategy",
        "strategy and operations",
        "strategy & operations"
    ],

    "operations": [
        "operations analyst",
        "operations associate",
        "business operations",
        "revenue operations",
        "sales operations",
        "product operations"
    ],

    "finance": [
        "financial analyst",
        "finance analyst",
        "strategic finance",
        "fp&a",
        "corporate development"
    ],

    "marketing_growth": [
        "marketing analyst",
        "growth analyst",
        "growth associate",
        "growth marketing",
        "marketing operations"
    ],

    "product": [
        "product analyst",
        "product associate",
        "product manager",
        "product operations"
    ],

    "software_engineering": [
        "software engineer",
        "software developer",
        "frontend engineer",
        "backend engineer",
        "full stack engineer"
    ],

    "data_science_ml": [
        "data scientist",
        "machine learning engineer",
        "ml engineer",
        "ai engineer"
    ]
}

ROLE_EXCLUSIONS = [
    "workplace operations",
    "people operations",
    "legal operations",
    "clinical operations",
    "security operations",
    "facilities operations"
]

SENIOR_TITLES = [
    "senior",
    "sr.",
    "manager",
    "director",
    "head of",
    "vice president",
    "vp",
    "principal",
    "lead"
]

ENTRY_TITLES = [
    "intern",
    "analyst",
    "associate",
    "coordinator",
    "specialist"
]


def find_role_families(target_roles):
    matched_families = []

    for target_role in target_roles:
        target_role = target_role.lower()

        for family, titles in ROLE_FAMILIES.items():
            if target_role in titles:
                if family not in matched_families:
                    matched_families.append(family)

    return matched_families


def calculate_role_match(job_title, target_roles):
    if pd.isna(job_title):
        return 0

    job_title = str(job_title).lower()

    for role in target_roles:
        role = role.lower()

        # Exact target role appears in job title
        if role in job_title:
            return 100

    return 0


def calculate_family_match(job_title, role_families):
    if pd.isna(job_title):
        return 0

    job_title = str(job_title).lower()

    # Exclude unrelated operations roles
    if any(exclusion in job_title for exclusion in ROLE_EXCLUSIONS):
        return 0

    for family in role_families:
        family_titles = ROLE_FAMILIES[family]

        for title in family_titles:
            if title in job_title:
                return 75

    return 0


def calculate_seniority_match(job_title):
    if pd.isna(job_title):
        return 0

    job_title = str(job_title).lower()

    # Clearly senior roles
    if any(title in job_title for title in SENIOR_TITLES):
        return 0

    # Clearly early-career roles
    if any(title in job_title for title in ENTRY_TITLES):
        return 100

    # Unclear / no seniority stated
    return 50


def calculate_skill_match(job_description, user_skills):
    if pd.isna(job_description):
        return 0

    description = str(job_description).lower()

    matched_skills = []

    for skill in user_skills:
        if skill.lower() in description:
            matched_skills.append(skill)

    if len(user_skills) == 0:
        return 0

    skill_score = (
        len(matched_skills) / len(user_skills)
    ) * 100

    return round(skill_score)


def calculate_industry_match(company_industry, preferred_industries):
    if pd.isna(company_industry):
        return 0

    company_industry = str(company_industry).lower()

    matched_industries = []

    for industry in preferred_industries:
        if industry.lower() in company_industry:
            matched_industries.append(industry)

    if len(preferred_industries) == 0:
        return 0

    industry_score = (
        len(matched_industries) / len(preferred_industries)
    ) * 100

    return round(industry_score)


def calculate_location_match(job_location, preferred_location):
    if pd.isna(job_location):
        return 0

    job_location = str(job_location).lower()
    preferred_location = preferred_location.lower()

    # New York variations
    if preferred_location == "new york":
        new_york_terms = [
            "new york",
            "nyc",
            "new york city"
        ]

        if any(term in job_location for term in new_york_terms):
            return 100

    # General location match
    if preferred_location in job_location:
        return 100

    # Remote jobs remain potentially accessible
    if "remote" in job_location:
        return 75

    return 0


def score_candidate_fit(latest_jobs, companies, user_profile, report=False):
    """Score jobs with the existing candidate-fit weights.

    Returns the same rows the Candidate_Fit sheet saves:
    role-family matches with Candidate_Fit_Score of at least 40.
    Passing report=True prints the same audit as the script.
    This function does not write the Excel workbook.
    """
    def _report(*args, **kwargs):
        if report:
            print(*args, **kwargs)

    latest_jobs = latest_jobs.copy()
    user_role_families = find_role_families(
        user_profile["target_roles"]
    )

    latest_jobs["Role_Match"] = latest_jobs["Job_Title"].apply(
        lambda title: calculate_role_match(
            title,
            user_profile["target_roles"]
        )
    )

    matched_jobs = latest_jobs[
        latest_jobs["Role_Match"] > 0
    ].copy()

    _report("\n=== ROLE MATCH RESULTS ===")
    _report("Matched Jobs:", len(matched_jobs))

    _report(
        matched_jobs[
            ["Company_Name", "Job_Title", "Location", "Role_Match"]
        ]
        .sort_values(["Role_Match", "Company_Name"], ascending=[False, True])
        .to_string(index=False)
    )

    latest_jobs["Family_Match"] = latest_jobs["Job_Title"].apply(
        lambda title: calculate_family_match(
            title,
            user_role_families
        )
    )

    family_matched_jobs = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ].copy()

    _report("\n=== ROLE FAMILY MATCH RESULTS ===")
    _report("Family Matched Jobs:", len(family_matched_jobs))

    _report(
        family_matched_jobs[
            ["Company_Name", "Job_Title", "Location", "Family_Match"]
        ]
        .sort_values(["Company_Name", "Job_Title"])
        .to_string(index=False)
    )

    latest_jobs["Seniority_Match"] = latest_jobs["Job_Title"].apply(
        calculate_seniority_match
    )

    _report("\n=== SENIORITY MATCH AUDIT ===")

    seniority_audit = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ][
        [
            "Company_Name",
            "Job_Title",
            "Family_Match",
            "Seniority_Match"
        ]
    ]

    _report(
        seniority_audit
        .sort_values(
            ["Seniority_Match", "Company_Name"],
            ascending=[False, True]
        )
        .to_string(index=False)
    )

    latest_jobs["Skill_Match"] = latest_jobs["Job_Description"].apply(
        lambda description: calculate_skill_match(
            description,
            user_profile["skills"]
        )
    )

    _report("\n=== SKILL MATCH AUDIT ===")

    skill_audit = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ][
        [
            "Company_Name",
            "Job_Title",
            "Family_Match",
            "Seniority_Match",
            "Skill_Match"
        ]
    ]

    _report(
        skill_audit
        .sort_values(
            ["Skill_Match", "Seniority_Match"],
            ascending=[False, False]
        )
        .to_string(index=False)
    )

    company_info = companies[
        [
            "Company_ID",
            "Industry"
        ]
    ].copy()

    latest_jobs = latest_jobs.merge(
        company_info,
        on="Company_ID",
        how="left"
    )

    _report("\n=== COMPANY INDUSTRY MERGE CHECK ===")

    _report(
        latest_jobs[
            [
                "Company_ID",
                "Company_Name",
                "Job_Title",
                "Industry"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    _report(
        "\nJobs missing industry:",
        latest_jobs["Industry"].isna().sum()
    )

    latest_jobs["Industry_Match"] = latest_jobs["Industry"].apply(
        lambda industry: calculate_industry_match(
            industry,
            user_profile["industries"]
        )
    )

    _report("\n=== INDUSTRY MATCH AUDIT ===")

    industry_audit = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ][
        [
            "Company_Name",
            "Job_Title",
            "Industry",
            "Industry_Match"
        ]
    ]

    _report(
        industry_audit
        .sort_values(
            ["Industry_Match", "Company_Name"],
            ascending=[False, True]
        )
        .to_string(index=False)
    )

    latest_jobs["Location_Match"] = latest_jobs["Location"].apply(
        lambda location: calculate_location_match(
            location,
            user_profile["location"]
        )
    )

    _report("\n=== LOCATION MATCH AUDIT ===")

    location_audit = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ][
        [
            "Company_Name",
            "Job_Title",
            "Location",
            "Location_Match"
        ]
    ]

    _report(
        location_audit
        .sort_values(
            ["Location_Match", "Company_Name"],
            ascending=[False, True]
        )
        .to_string(index=False)
    )

    latest_jobs["Candidate_Fit_Score"] = (
        latest_jobs["Family_Match"] * 0.35
        + latest_jobs["Seniority_Match"] * 0.25
        + latest_jobs["Skill_Match"] * 0.20
        + latest_jobs["Industry_Match"] * 0.10
        + latest_jobs["Location_Match"] * 0.10
    ).round(1)

    # Only rank jobs that belong to the user's target role families
    recommended_jobs = latest_jobs[
        latest_jobs["Family_Match"] > 0
    ].copy()

    recommended_jobs = recommended_jobs.sort_values(
        "Candidate_Fit_Score",
        ascending=False
    )

    _report("\n=== TOP 20 CANDIDATE FIT RESULTS ===")

    _report(
        recommended_jobs[
            [
                "Company_Name",
                "Job_Title",
                "Location",
                "Family_Match",
                "Seniority_Match",
                "Skill_Match",
                "Industry_Match",
                "Location_Match",
                "Candidate_Fit_Score"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    candidate_fit_output = recommended_jobs[
        [
            "Snapshot_Date",
            "Company_ID",
            "Company_Name",
            "Job_ID",
            "Job_Title",
            "Location",
            "Job_URL",
            "Industry",
            "Family_Match",
            "Seniority_Match",
            "Skill_Match",
            "Industry_Match",
            "Location_Match",
            "Candidate_Fit_Score"
        ]
    ].copy()

    # Only keep reasonably relevant jobs
    candidate_fit_output = candidate_fit_output[
        candidate_fit_output["Candidate_Fit_Score"] >= 40
    ]

    return candidate_fit_output


def main():
    user_role_families = find_role_families(
        user_profile["target_roles"]
    )

    print("\n=== USER ROLE FAMILIES ===")
    print(user_role_families)

    print("=== USER PROFILE ===")
    print("Target Roles:", user_profile["target_roles"])
    print("Skills:", user_profile["skills"])
    print("Industries:", user_profile["industries"])
    print("Location:", user_profile["location"])

    jobs = pd.read_excel(FILE_PATH, sheet_name="Job_Snapshots")

    jobs["Snapshot_Date"] = pd.to_datetime(jobs["Snapshot_Date"])

    latest_date = jobs["Snapshot_Date"].max()

    latest_jobs = jobs[
        jobs["Snapshot_Date"] == latest_date
    ].copy()

    print("\n=== LATEST JOB SNAPSHOT ===")
    print("Snapshot Date:", latest_date.date())
    print("Total Jobs:", len(latest_jobs))
    print("Companies:", latest_jobs["Company_ID"].nunique())

    companies = pd.read_excel(
        FILE_PATH,
        sheet_name="Companies"
    )

    candidate_fit_output = score_candidate_fit(
        latest_jobs,
        companies,
        user_profile,
        report=True
    )

    with pd.ExcelWriter(
        FILE_PATH,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:
        candidate_fit_output.to_excel(
            writer,
            sheet_name="Candidate_Fit",
            index=False
        )

    print("\n=== CANDIDATE FIT SAVED ===")
    print("Jobs saved:", len(candidate_fit_output))
    print("Sheet: Candidate_Fit")


if __name__ == "__main__":
    main()
