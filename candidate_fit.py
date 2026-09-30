import re

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

    # One of EXPERIENCE_LEVELS: "entry", "mid", or "senior".
    "experience_level": "entry",

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

# ==========================================
# WHOLE-WORD MATCHING
# Terms match only as whole words, so "excel" does not match
# "excellent", "ai" does not match "supply chain", and "intern"
# does not match "international". A term may contain spaces or
# symbols ("fp&a", "c++", "head of"); it just cannot sit inside
# a longer word.
# ==========================================


def contains_term(text, term):
    """Return True when term appears in text as a whole word or phrase."""
    if text is None or term is None:
        return False
    if isinstance(text, float) and pd.isna(text):
        return False

    term = str(term).strip().lower()
    if not term:
        return False

    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, str(text).lower()) is not None


def supported_roles():
    """Every role phrase HiddenHire can match, in role-family order."""
    roles = []
    for titles in ROLE_FAMILIES.values():
        for title in titles:
            if title not in roles:
                roles.append(title)
    return roles


# ==========================================
# SENIORITY
# A title is classified as senior, mid, entry, or unknown. The
# first group with a whole-word hit wins, in that order, so
# "Senior Associate" is senior and "Associate Product Manager"
# is entry. The level is then scored against the user's chosen
# experience level.
# ==========================================

EXPERIENCE_LEVELS = ["entry", "mid", "senior"]

SENIOR_TITLES = [
    "senior",
    "sr",
    "sr.",
    "staff",
    "principal",
    "lead",
    "head of",
    "director",
    "vice president",
    "vp",
    "chief",
]

ENTRY_TITLES = [
    "intern",
    "internship",
    "new grad",
    "graduate",
    "junior",
    "jr",
    "entry level",
    "entry-level",
    "apprentice",
    "analyst",
    "associate",
    "coordinator",
    "specialist",
]

MID_TITLES = [
    "manager",
    "ii",
    "iii",
]

# Rows: the user's experience level. Columns: the title's level.
# Unknown titles score 50 for everyone, as before.
SENIORITY_SCORES = {
    "entry": {"entry": 100, "mid": 40, "senior": 0, "unknown": 50},
    "mid": {"entry": 50, "mid": 100, "senior": 40, "unknown": 50},
    "senior": {"entry": 0, "mid": 50, "senior": 100, "unknown": 50},
}


def classify_seniority(job_title):
    """Return "senior", "entry", "mid", or "unknown" for a job title."""
    if job_title is None or (isinstance(job_title, float) and pd.isna(job_title)):
        return "unknown"

    # "Member of Technical Staff" / "Member of GTM Staff" is a generic
    # startup title, not a staff-level (senior) role.
    title = re.sub(r"member of [\w\s&]*?staff", " ", str(job_title).lower())
    for level, terms in [
        ("senior", SENIOR_TITLES),
        ("entry", ENTRY_TITLES),
        ("mid", MID_TITLES),
    ]:
        if any(contains_term(title, term) for term in terms):
            return level
    return "unknown"


def normalize_experience_level(experience_level):
    """Map a user's experience level to "entry", "mid", or "senior"."""
    level = str(experience_level or "entry").strip().lower()
    for option in EXPERIENCE_LEVELS:
        if level.startswith(option):
            return option
    return "entry"


def find_role_families(target_roles):
    matched_families = []

    for target_role in target_roles:
        target_role = target_role.lower()

        for family, titles in ROLE_FAMILIES.items():
            if target_role in titles:
                if family not in matched_families:
                    matched_families.append(family)

    return matched_families


def is_excluded_title(job_title):
    """True for titles in unrelated operations families."""
    return any(
        contains_term(job_title, exclusion)
        for exclusion in ROLE_EXCLUSIONS
    )


def calculate_role_match(job_title, target_roles):
    """100 when a target role appears in the title as a whole phrase."""
    if job_title is None or (isinstance(job_title, float) and pd.isna(job_title)):
        return 0

    if is_excluded_title(job_title):
        return 0

    for role in target_roles:
        if contains_term(job_title, role):
            return 100

    return 0


def calculate_family_match(job_title, role_families):
    """75 when the title belongs to one of the user's role families."""
    if job_title is None or (isinstance(job_title, float) and pd.isna(job_title)):
        return 0

    # Exclude unrelated operations roles
    if is_excluded_title(job_title):
        return 0

    for family in role_families:
        for title in ROLE_FAMILIES[family]:
            if contains_term(job_title, title):
                return 75

    return 0


def calculate_title_match(role_match, family_match):
    """Title component of fit: 100 for an exact target role, else family."""
    if family_match > 0 and role_match > 0:
        return 100
    return family_match


def calculate_seniority_match(job_title, experience_level="entry"):
    level = normalize_experience_level(experience_level)
    return SENIORITY_SCORES[level][classify_seniority(job_title)]


def matched_skills(job_description, user_skills):
    """Skills from the user's list that appear in the description."""
    return [
        skill for skill in user_skills
        if contains_term(job_description, skill)
    ]


def calculate_skill_match(job_description, user_skills):
    """Share of the user's skills found in the posting, 0-100."""
    if len(user_skills) == 0:
        return 0
    if job_description is None or (
        isinstance(job_description, float) and pd.isna(job_description)
    ):
        return 0

    found = matched_skills(job_description, user_skills)
    return round(len(found) / len(user_skills) * 100)


def matched_industries(company_industry, preferred_industries):
    """Preferred industries that appear in the company's industry label."""
    return [
        industry for industry in preferred_industries
        if contains_term(company_industry, industry)
    ]


def calculate_industry_match(company_industry, preferred_industries):
    """100 when the company is in any preferred industry, else 0.

    Listing more preferred industries widens the search. It no longer
    lowers the score of a company that matches one of them.
    """
    if matched_industries(company_industry, preferred_industries):
        return 100
    return 0


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
    """Score jobs for one candidate profile.

    Candidate_Fit_Score = 35% title (100 for an exact target role,
    75 for another title in the same role family), 25% seniority
    against the profile's experience_level, 20% skills, 10% industry,
    and 10% location.

    Returns the same rows the Candidate_Fit sheet saves:
    role-family matches with Candidate_Fit_Score of at least 40,
    leaving out titles two levels away from the user's experience
    level (for example, Director roles in an entry-level search).
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

    experience_level = user_profile.get("experience_level", "entry")
    latest_jobs["Seniority_Match"] = latest_jobs["Job_Title"].apply(
        lambda title: calculate_seniority_match(title, experience_level)
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

    latest_jobs["Title_Match"] = [
        calculate_title_match(role, family)
        for role, family in zip(
            latest_jobs["Role_Match"],
            latest_jobs["Family_Match"],
        )
    ]

    latest_jobs["Candidate_Fit_Score"] = (
        latest_jobs["Title_Match"] * 0.35
        + latest_jobs["Seniority_Match"] * 0.25
        + latest_jobs["Skill_Match"] * 0.20
        + latest_jobs["Industry_Match"] * 0.10
        + latest_jobs["Location_Match"] * 0.10
    ).round(1)

    # Only rank jobs that belong to the user's target role families.
    # Seniority_Match of 0 means the title is two levels away from the
    # user's experience level (a senior title for an entry-level search,
    # or the reverse), so those jobs are left out.
    recommended_jobs = latest_jobs[
        (latest_jobs["Family_Match"] > 0)
        & (latest_jobs["Seniority_Match"] > 0)
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
            "Role_Match",
            "Family_Match",
            "Title_Match",
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
    print("Experience level:", user_profile["experience_level"])

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
