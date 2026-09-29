import html

import pandas as pd
import streamlit as st

import candidate_fit
from pipeline import rank_hidden_opportunities

st.set_page_config(
    page_title="HiddenHire",
    layout="wide",
)

st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .stApp {
            background: #f4f6f8;
            color: #17212b;
        }
        header[data-testid="stHeader"] {
            background: transparent;
        }
        [data-testid="stToolbar"] {
            display: none;
        }
        footer {
            display: none;
        }
        .block-container {
            max-width: 920px;
            padding-top: 3.2rem;
            padding-bottom: 4rem;
        }
        h1 {
            color: #12202c !important;
            font-size: 2.6rem !important;
            font-weight: 680 !important;
            letter-spacing: -0.045em;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }
        h2 {
            color: #12202c !important;
            font-weight: 650 !important;
            letter-spacing: -0.03em;
            margin-top: 0.2rem;
        }
        .tagline {
            color: #1e465c;
            font-size: 1.28rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 0 0 0.45rem 0;
        }
        .lead {
            color: #243847;
            font-size: 1.05rem;
            line-height: 1.55;
            margin: 0 0 0.35rem 0;
        }
        .description {
            color: #5c6d7a;
            font-size: 0.98rem;
            line-height: 1.55;
            margin: 0 0 1rem 0;
        }
        .section-label {
            color: #5c6d7a;
            font-size: 0.75rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 1.3rem 0 0.45rem 0;
        }
        div[data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #e3e8ee;
            border-radius: 18px;
            padding: 0.35rem 1.15rem 0.85rem;
            box-shadow: 0 10px 30px rgba(18, 32, 44, 0.04);
        }
        [data-testid="stWidgetLabel"] p {
            color: #243140 !important;
            font-weight: 600 !important;
        }
        [data-testid="stTextInput"] input {
            background: #f8fafb !important;
            color: #17212b !important;
            border: 1px solid #d7e0e7 !important;
            border-radius: 10px !important;
        }
        div[data-testid="stFormSubmitButton"] button {
            background: #0e4c5c;
            color: #ffffff;
            border: none;
            border-radius: 10px;
            font-weight: 650;
            padding: 0.55rem 1rem;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background: #0b3e4b;
            color: #ffffff;
        }
        [data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e3e8ee !important;
            border-radius: 14px !important;
        }
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary {
            background: #ffffff !important;
            color: #243140 !important;
        }
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span,
        [data-testid="stExpander"] details p {
            color: #243140 !important;
        }
        .method-row {
            display: grid;
            grid-template-columns: 11.5rem 1fr;
            gap: 0.35rem 1rem;
            padding: 0.35rem 0;
            color: #243140;
        }
        .method-name {
            font-weight: 700;
        }
        .method-copy {
            color: #4d5f6c;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border: 1px solid #e3e8ee !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 24px rgba(18, 32, 44, 0.035);
        }
        .job-title {
            color: #12202c;
            font-size: 1.18rem;
            font-weight: 680;
            letter-spacing: -0.02em;
            margin: 0;
        }
        .company-name {
            color: #0e4c5c;
            font-size: 0.98rem;
            font-weight: 600;
            margin: 0.2rem 0 0.15rem 0;
        }
        .detail {
            color: #5c6d7a;
            margin: 0;
        }
        .why-label {
            color: #5c6d7a;
            font-size: 0.75rem;
            font-weight: 650;
            letter-spacing: 0.04em;
            margin: 0.95rem 0 0.28rem 0;
        }
        .why-copy {
            color: #243847;
            font-size: 0.95rem;
            line-height: 1.5;
            margin: 0;
        }
        .score-row {
            display: flex;
            gap: 0.55rem;
            margin-top: 0.85rem;
        }
        .chip {
            background: #f5f8fa;
            border: 1px solid #e3e8ee;
            border-radius: 12px;
            min-width: 8.4rem;
            padding: 0.42rem 0.7rem 0.38rem;
        }
        .chip-label {
            display: block;
            color: #667886;
            font-size: 0.68rem;
            font-weight: 650;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .chip-value {
            display: block;
            color: #173042;
            font-size: 1.12rem;
            font-weight: 720;
            margin-top: 0.05rem;
        }
        .score-panel {
            background: #f3f8fa;
            border: 1px solid #d7e7ee;
            border-radius: 14px;
            padding: 0.7rem 0.55rem 0.65rem;
            text-align: center;
        }
        .score-label {
            color: #5d7684;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin: 0;
        }
        .score-value {
            color: #0e4c5c;
            font-size: 2.15rem;
            font-weight: 740;
            letter-spacing: -0.04em;
            line-height: 1;
            margin: 0.28rem 0 0 0;
        }
        div[data-testid="stLinkButton"] a {
            background: #0e4c5c;
            border: none;
            border-radius: 999px;
            color: #ffffff !important;
            font-weight: 650;
            padding: 0.38rem 0.95rem;
            text-decoration: none;
        }
        div[data-testid="stLinkButton"] a:hover {
            background: #0b3e4b;
            color: #ffffff !important;
        }
        div[data-testid="stLinkButton"] {
            margin-top: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def split_csv(text):
    return [item.strip() for item in text.split(",") if item.strip()]


def show_text(value):
    if value is None or (isinstance(value, float) and value != value):
        return "—"
    text = str(value).strip()
    return text if text else "—"


FAMILY_LABELS = {
    "business_analytics": "business analytics",
    "strategy": "strategy",
    "operations": "operations",
    "finance": "finance",
    "marketing_growth": "marketing and growth",
    "product": "product",
    "software_engineering": "software engineering",
    "data_science_ml": "data and machine learning",
}


def join_phrases(items):
    items = [item for item in items if item]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def matched_family_labels(job_title, target_roles):
    title = "" if job_title is None else str(job_title).lower()
    if any(exclusion in title for exclusion in candidate_fit.ROLE_EXCLUSIONS):
        return []

    labels = []
    families = candidate_fit.find_role_families(
        [role.lower() for role in target_roles]
    )
    for family in families:
        phrases = candidate_fit.ROLE_FAMILIES[family]
        if any(phrase in title for phrase in phrases):
            labels.append(FAMILY_LABELS[family])
    return labels


def row_value(row, name):
    """Read one result field from a Series or an itertuples row.

    Streamlit Cloud can hand back a row whose match-score attributes
    are missing even when the original column exists. A missing or
    null value means that signal is not available.
    """
    value = None
    getter = getattr(row, "get", None)
    if callable(getter):
        try:
            value = getter(name, None)
        except TypeError:
            value = None
    if value is None and hasattr(row, "_asdict"):
        value = row._asdict().get(name)
    if value is None:
        value = getattr(row, name, None)
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return value


def signal_above(row, name, threshold):
    value = row_value(row, name)
    if value is None:
        return False
    try:
        return float(value) > threshold
    except (TypeError, ValueError):
        return False


def signal_at_least(row, name, threshold):
    value = row_value(row, name)
    if value is None:
        return False
    try:
        return float(value) >= threshold
    except (TypeError, ValueError):
        return False


def explain_opportunity(row, profile):
    """Describe signals the current scores already support."""
    title_value = row_value(row, "Job_Title")
    industry_value = row_value(row, "Industry")
    title = "" if title_value is None else str(title_value)
    industry_text = "" if industry_value is None else str(industry_value)
    target_roles = profile.get("target_roles", [])
    preferred_industries = profile.get("industries", [])
    preferred_location = profile.get("location", "")

    exact_roles = [
        role for role in target_roles
        if role and role.lower() in title.lower()
    ]
    if exact_roles:
        noun = "role" if len(exact_roles) == 1 else "roles"
        role_phrase = f"your target {join_phrases(exact_roles)} {noun}"
    else:
        family_labels = matched_family_labels(title, target_roles)
        if family_labels:
            role_phrase = f"your target {join_phrases(family_labels)} roles"
        elif signal_above(row, "Family_Match", 0):
            role_phrase = "your target roles"
        else:
            role_phrase = ""

    industry_hits = [
        industry for industry in preferred_industries
        if industry and industry.lower() in industry_text.lower()
    ]
    if signal_above(row, "Industry_Match", 0) and industry_hits:
        noun = "industry" if len(industry_hits) == 1 else "industries"
        industry_phrase = f"your preferred {join_phrases(industry_hits)} {noun}"
    else:
        industry_phrase = ""

    if signal_at_least(row, "Skill_Match", 100):
        skill_phrase = "your listed skills in the posting"
    elif signal_above(row, "Skill_Match", 0):
        skill_phrase = "some of your listed skills in the posting"
    else:
        skill_phrase = ""

    if signal_at_least(row, "Location_Match", 100) and preferred_location:
        location_phrase = f"a location that fits your {preferred_location} preference"
    elif signal_at_least(row, "Location_Match", 75):
        location_phrase = "a remote posting that may still fit your location preference"
    else:
        location_phrase = ""

    fit_points = [phrase for phrase in [role_phrase, industry_phrase] if phrase]
    extra_points = [phrase for phrase in [skill_phrase, location_phrase] if phrase]
    # Keep the card to the strongest supported signals.
    if len(fit_points) >= 2 and len(extra_points) > 1:
        extra_points = extra_points[:1]

    if len(fit_points) >= 2:
        fit_sentence = "Strong match for " + join_phrases(fit_points)
    elif fit_points:
        fit_sentence = "This role lines up with " + fit_points[0]
    else:
        fit_sentence = "This opening matches part of your search"

    if extra_points:
        fit_sentence += ", with " + join_phrases(extra_points)
    fit_sentence += "."

    momentum = row_value(row, "Hiring_Momentum_Score")
    if momentum is None:
        momentum_sentence = (
            "Hiring activity for this company is not available in the current data."
        )
    elif momentum >= 60:
        momentum_sentence = (
            "The company's current hiring activity makes this "
            "an opportunity worth exploring now."
        )
    elif momentum >= 45:
        momentum_sentence = (
            "Hiring activity looks steady compared with "
            "the other companies in this search."
        )
    else:
        momentum_sentence = (
            "Hiring activity is quieter than "
            "the other companies in this search."
        )

    return f"{fit_sentence} {momentum_sentence}"


st.markdown("# HiddenHire")
st.markdown(
    '<p class="tagline">Discover emerging companies hiring for you.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="lead">Discover overlooked opportunities by combining your '
    "candidate fit with real hiring momentum.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="description">HiddenHire combines candidate fit with real hiring '
    "momentum to surface opportunities you might otherwise miss.</p>",
    unsafe_allow_html=True,
)

with st.expander("How the scores work"):
    st.markdown(
        """
        <div class="method-row">
            <div class="method-name">Candidate Fit</div>
            <div class="method-copy">How well the role matches your profile.</div>
        </div>
        <div class="method-row">
            <div class="method-name">Hiring Momentum</div>
            <div class="method-copy">Recent hiring activity at the company.</div>
        </div>
        <div class="method-row">
            <div class="method-name">Hidden Opportunity</div>
            <div class="method-copy">60% Candidate Fit + 40% Hiring Momentum.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<p class="section-label">Your profile</p>', unsafe_allow_html=True)

with st.form("profile"):
    left, right = st.columns(2)
    with left:
        target_roles_text = st.text_input(
            "Target Roles",
            value="business analyst, strategy analyst, operations analyst",
            help="Separate roles with commas.",
        )
        skills_text = st.text_input(
            "Skills",
            value="SQL, Excel, Tableau, Python",
            help="Separate skills with commas.",
        )
    with right:
        industries_text = st.text_input(
            "Preferred Industries",
            value="fintech, AI, enterprise software",
            help="Separate industries with commas.",
        )
        location = st.text_input(
            "Preferred Location",
            value="New York",
        )
    submitted = st.form_submit_button(
        "Find Hidden Opportunities",
        type="primary",
    )

if submitted:
    with st.spinner("Finding hidden opportunities..."):
        profile = {
            "target_roles": split_csv(target_roles_text),
            "skills": split_csv(skills_text),
            "industries": split_csv(industries_text),
            "location": location.strip(),
        }
        results = rank_hidden_opportunities(
            profile["target_roles"],
            profile["skills"],
            profile["industries"],
            profile["location"],
        )
        results = results.sort_values(
            [
                "Hidden_Opportunity_Score",
                "Candidate_Fit_Score",
                "Company_Name",
                "Job_Title",
            ],
            ascending=[False, False, True, True],
        )
        st.session_state["results"] = results.reset_index(drop=True)
        st.session_state["search_profile"] = profile

results = st.session_state.get("results")

if results is None:
    st.caption("Enter a profile, then find opportunities.")
elif results.empty:
    st.info("No matched opportunities for this profile.")
else:
    count = len(results)
    label = "opportunity" if count == 1 else "opportunities"
    st.markdown('<p class="section-label">Results</p>', unsafe_allow_html=True)
    st.subheader(f"{count} matched {label}")

    for position, row in enumerate(results.itertuples(index=False)):
        with st.container(border=True):
            info, score = st.columns([4.4, 1.35], vertical_alignment="center")
            with info:
                st.markdown(
                    f'<p class="job-title">{html.escape(show_text(row.Job_Title))}</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<p class="company-name">{html.escape(show_text(row.Company_Name))}</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<p class="detail">{html.escape(show_text(row.Location))}'
                    f" · {html.escape(show_text(row.Industry))}</p>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""
                    <div class="score-row">
                        <div class="chip">
                            <span class="chip-label">Candidate Fit</span>
                            <span class="chip-value">{row.Candidate_Fit_Score:.1f}</span>
                        </div>
                        <div class="chip">
                            <span class="chip-label">Hiring Momentum</span>
                            <span class="chip-value">{row.Hiring_Momentum_Score:.1f}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                job_url = show_text(row.Job_URL)
                if job_url != "—":
                    st.link_button("View Job", job_url)
            with score:
                st.markdown(
                    f"""
                    <div class="score-panel">
                        <p class="score-label">Hidden Opportunity</p>
                        <p class="score-value">{row.Hidden_Opportunity_Score:.1f}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            explanation = explain_opportunity(
                results.iloc[position],
                st.session_state.get("search_profile", {}),
            )
            st.markdown(
                '<p class="why-label">Why this opportunity?</p>'
                f'<p class="why-copy">{html.escape(explanation)}</p>',
                unsafe_allow_html=True,
            )
