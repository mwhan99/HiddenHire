import html

import streamlit as st

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
        results = rank_hidden_opportunities(
            split_csv(target_roles_text),
            split_csv(skills_text),
            split_csv(industries_text),
            location.strip(),
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

    for row in results.itertuples(index=False):
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
