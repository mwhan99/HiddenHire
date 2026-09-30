import pandas as pd

import candidate_fit as cf


# ------------------------------------------
# Fix 1: whole-word matching
# ------------------------------------------

def test_excel_does_not_match_excellent():
    description = "Excellent communication and a passion for excellence."
    assert cf.calculate_skill_match(description, ["Excel"]) == 0


def test_excel_matches_as_a_word():
    description = "Advanced Excel (pivot tables) and SQL."
    assert cf.calculate_skill_match(description, ["Excel", "SQL"]) == 100


def test_skills_with_symbols_match():
    assert cf.contains_term("Experience with C++ and FP&A models", "c++")
    assert cf.contains_term("Experience with C++ and FP&A models", "FP&A")


def test_ai_does_not_match_inside_other_words():
    assert cf.calculate_industry_match("Supply Chain / SaaS / FoodTech", ["AI"]) == 0
    assert cf.calculate_industry_match("Retail / E-commerce", ["AI"]) == 0


def test_ai_matches_as_an_industry():
    assert cf.calculate_industry_match("AI / Healthcare / Enterprise Software", ["AI"]) == 100


def test_missing_description_scores_zero():
    assert cf.calculate_skill_match(None, ["SQL"]) == 0
    assert cf.calculate_skill_match(float("nan"), ["SQL"]) == 0


# ------------------------------------------
# Fix 5: more preferences do not lower scores
# ------------------------------------------

def test_one_matching_industry_gets_full_credit():
    preferences = ["fintech", "AI", "enterprise software"]
    assert cf.calculate_industry_match("FinTech / Banking", preferences) == 100


def test_no_matching_industry_scores_zero():
    assert cf.calculate_industry_match("HealthTech", ["fintech", "AI"]) == 0
    assert cf.calculate_industry_match(None, ["fintech"]) == 0


def test_skills_stay_a_share_of_the_list():
    description = "We use SQL and Python daily."
    assert cf.calculate_skill_match(description, ["SQL", "Python", "Tableau", "Excel"]) == 50


# ------------------------------------------
# Fix 3: seniority
# ------------------------------------------

def test_international_is_not_an_internship():
    assert cf.classify_seniority("Product Manager, International") == "mid"
    assert cf.classify_seniority("Software Engineer, International") == "unknown"


def test_title_levels():
    assert cf.classify_seniority("Software Engineer Internship") == "entry"
    assert cf.classify_seniority("Senior Business Analyst") == "senior"
    assert cf.classify_seniority("Sr. Associate, Strategy") == "senior"
    assert cf.classify_seniority("Associate Product Manager") == "entry"
    assert cf.classify_seniority("Software Engineer II") == "mid"
    assert cf.classify_seniority("Leadership Programs Analyst") == "entry"
    assert cf.classify_seniority("Staff Software Engineer") == "senior"
    assert cf.classify_seniority("Member of GTM Staff, Founding Revenue Operations") == "unknown"
    assert cf.classify_seniority("Chief of Staff") == "senior"


def test_seniority_follows_experience_level():
    assert cf.calculate_seniority_match("Business Analyst", "entry") == 100
    assert cf.calculate_seniority_match("Senior Business Analyst", "entry") == 0
    assert cf.calculate_seniority_match("Senior Business Analyst", "senior") == 100
    assert cf.calculate_seniority_match("Product Manager", "mid") == 100
    assert cf.calculate_seniority_match("Product Manager", "entry") == 40


def test_experience_level_labels_are_accepted():
    assert cf.normalize_experience_level("Entry level / internship") == "entry"
    assert cf.normalize_experience_level("Mid level") == "mid"
    assert cf.normalize_experience_level(None) == "entry"


# ------------------------------------------
# Fix 4: exact title credit
# ------------------------------------------

def test_exact_role_beats_family_match():
    families = cf.find_role_families(["business analyst"])
    exact = cf.calculate_title_match(
        cf.calculate_role_match("Business Analyst", ["business analyst"]),
        cf.calculate_family_match("Business Analyst", families),
    )
    related = cf.calculate_title_match(
        cf.calculate_role_match("Data Analyst", ["business analyst"]),
        cf.calculate_family_match("Data Analyst", families),
    )
    assert exact == 100
    assert related == 75


def test_excluded_titles_get_no_role_credit():
    families = cf.find_role_families(["operations analyst"])
    title = "People Operations Analyst"
    assert cf.calculate_role_match(title, ["operations analyst"]) == 0
    assert cf.calculate_family_match(title, families) == 0


# ------------------------------------------
# Fix 2: the role list covers every role family
# ------------------------------------------

def test_every_supported_role_maps_to_a_family():
    for role in cf.supported_roles():
        assert cf.find_role_families([role]), role


# ------------------------------------------
# End to end
# ------------------------------------------

def _jobs():
    return pd.DataFrame(
        {
            "Snapshot_Date": ["2026-09-30"] * 4,
            "Company_ID": ["C1", "C1", "C2", "C2"],
            "Company_Name": ["Acme", "Acme", "Beta", "Beta"],
            "Job_ID": ["1", "2", "3", "4"],
            "Job_Title": [
                "Business Analyst",
                "Data Analyst",
                "Senior Business Analyst",
                "People Operations Analyst",
            ],
            "Location": ["New York, NY"] * 4,
            "Job_URL": ["https://example.com"] * 4,
            "Job_Description": [
                "SQL and Excel required.",
                "SQL and Excel required.",
                "SQL and Excel required.",
                "SQL and Excel required.",
            ],
        }
    )


def _companies():
    return pd.DataFrame(
        {
            "Company_ID": ["C1", "C2"],
            "Industry": ["FinTech / AI", "Supply Chain / SaaS"],
        }
    )


def test_score_candidate_fit_end_to_end():
    profile = {
        "target_roles": ["business analyst"],
        "skills": ["SQL", "Excel"],
        "industries": ["AI"],
        "location": "New York",
        "experience_level": "entry",
    }
    scored = cf.score_candidate_fit(_jobs(), _companies(), profile)
    scores = dict(zip(scored["Job_Title"], scored["Candidate_Fit_Score"]))

    # 35 title + 25 seniority + 20 skills + 10 industry + 10 location
    assert scores["Business Analyst"] == 100.0
    # Same family, not the exact role: 75% of the title component.
    # 26.25 + 25 + 20 + 10 + 10 = 91.25, stored rounded to one decimal.
    assert abs(scores["Data Analyst"] - 91.25) <= 0.05
    # Senior titles are left out of an entry-level search.
    assert "Senior Business Analyst" not in scores
    assert "People Operations Analyst" not in scores


def test_senior_search_keeps_senior_roles():
    profile = {
        "target_roles": ["business analyst"],
        "skills": ["SQL", "Excel"],
        "industries": ["AI"],
        "location": "New York",
        "experience_level": "senior",
    }
    scored = cf.score_candidate_fit(_jobs(), _companies(), profile)
    scores = dict(zip(scored["Job_Title"], scored["Candidate_Fit_Score"]))

    # 35 title + 25 seniority + 20 skills + 0 industry + 10 location.
    # "ai" does not match Beta's "Supply Chain / SaaS" industry.
    assert scores["Senior Business Analyst"] == 90.0
    # Entry-level titles are left out of a senior search.
    assert "Business Analyst" not in scores
