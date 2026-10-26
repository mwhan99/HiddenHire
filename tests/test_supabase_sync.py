import json

import pandas as pd

import supabase_sync as sync


def _companies():
    return pd.DataFrame({
        "Company_ID": ["A", "B", "X"],
        "Company_Name": ["Company A", "Company B", "Company X"],
        "Industry": ["AI / FinTech", "HealthTech", "AI"],
        "ATS": ["Ashby", "Greenhouse", "Gem"],
        "Date_Added": pd.to_datetime(["2026-09-18"] * 3),
        "Active": [True, True, False],
    })


def _jobs():
    rows = []

    def add(date, company, job_id, title, description="SQL and Excel"):
        rows.append({
            "Snapshot_Date": pd.Timestamp(date),
            "Company_ID": company,
            "Company_Name": f"Company {company}",
            "Job_ID": job_id,
            "Job_Title": title,
            "Location": "New York, NY",
            "Date_Posted": "2026-09-01T11:49:05.881+00:00",
            "Job_URL": f"https://example.com/{job_id}",
            "Job_Description": description,
            "ATS": "Ashby" if company == "A" else "Greenhouse",
        })

    add("2026-09-28", "A", "a1", "Business Analyst", "old text")
    add("2026-09-28", "B", 6598283003.0, "Senior Software Engineer")
    add("2026-10-05", "A", "a1", "Business Analyst", "new text")
    add("2026-10-05", "A", "a2", "People Operations Associate")
    add("2026-10-05", "B", 6598283003.0, "Senior Software Engineer")
    return pd.DataFrame(rows)


def test_clean_makes_plain_json_values():
    assert sync.clean(float("nan")) is None
    assert sync.clean(pd.NA) is None
    assert sync.clean(pd.Series([3]).iloc[0]) == 3
    assert sync.clean({"when": pd.Timestamp("2026-10-19")}) == {"when": "2026-10-19T00:00:00"}


def test_numeric_job_ids_match_the_scoring_keys():
    assert sync.job_id_text(6598283003.0) == "6598283003"
    assert sync.job_id_text(6598283003) == "6598283003"
    assert sync.job_id_text(" abc ") == "abc"
    assert sync.job_id_text(None) is None


def test_date_posted_formats_are_read():
    assert sync.timestamp("2025-06-03T17:44:13-04:00") == "2025-06-03T21:44:13+00:00"
    assert sync.timestamp(pd.Timestamp("2026-02-23 20:57:15")) == "2026-02-23T20:57:15+00:00"
    assert sync.timestamp(None) is None
    assert sync.timestamp("not a date") is None


def test_role_families_follow_candidate_fit_rules():
    assert sync.role_families("Business Analyst") == ["business_analytics"]
    assert sync.role_families("Product Operations Manager") == ["operations", "product"]
    # Excluded operations titles belong to no family.
    assert sync.role_families("People Operations Associate") == []
    assert sync.role_families(None) == []


def test_job_snapshot_rows_add_labels():
    rows = sync.job_snapshot_rows(_jobs())
    first = rows[0]
    assert first["snapshot_date"] == "2026-09-28"
    assert first["role_families"] == ["business_analytics"]
    assert first["seniority"] == "entry"
    assert first["job_function"] == "Data & Analytics"
    assert "job_description" not in first
    assert rows[1]["job_id"] == "6598283003"
    assert rows[1]["seniority"] == "senior"


def test_descriptions_keep_the_latest_text_once_per_job():
    rows = sync.description_rows(_jobs())
    by_key = {(row["company_id"], row["job_id"]): row for row in rows}
    assert len(rows) == 3
    assert by_key[("A", "a1")]["description"] == "new text"
    assert by_key[("A", "a1")]["last_seen"] == "2026-10-05"
    assert by_key[("B", "6598283003")]["last_seen"] == "2026-10-05"


def test_build_tables_matches_market_insights():
    tables = sync.build_tables(_companies(), _jobs())

    # Every table is valid JSON with unique primary keys.
    for name, rows in tables.items():
        json.dumps(rows, allow_nan=False)
        keys = [tuple(row[column] for column in sync.PRIMARY_KEYS[name]) for row in rows]
        assert len(keys) == len(set(keys)), name

    assert [row["company_id"] for row in tables["companies"]] == ["A", "B", "X"]
    # updated_at is sent on every sync, not only when a row is first added.
    stamps = {row["updated_at"] for row in tables["companies"] + tables["market_summary"]}
    assert len(stamps) == 1 and stamps.pop().endswith("+00:00")
    assert tables["companies"][2]["active"] is False
    assert tables["companies"][0]["date_added"] == "2026-09-18"

    # First date has nothing to compare with.
    first = [row for row in tables["company_momentum"] if row["snapshot_date"] == "2026-09-28"]
    assert {row["momentum"] for row in first} == {"New to tracking"}
    assert all(row["net_change"] is None for row in first)

    latest = {
        row["company_id"]: row for row in tables["company_momentum"]
        if row["snapshot_date"] == "2026-10-05"
    }
    assert latest["A"]["open_now"] == 2
    assert latest["A"]["net_change"] == 1
    assert latest["A"]["new_roles"] == 1
    assert latest["A"]["trend"] == [1, 2]
    assert latest["A"]["new_postings"] == [{
        "job_title": "People Operations Associate",
        "location": "New York, NY",
        "job_url": "https://example.com/a2",
    }]
    assert latest["A"]["rank"] == 1
    assert latest["B"]["momentum"] == "Steady"

    summaries = {row["snapshot_date"]: row for row in tables["market_summary"]}
    assert summaries["2026-09-28"]["headline"]["previous_date"] is None
    headline = summaries["2026-10-05"]["headline"]
    assert headline["open_roles"] == 3
    assert headline["new_roles"] == 1
    assert summaries["2026-10-05"]["coverage"] == {
        "curated": 3, "active": 2, "by_ats": {"Ashby": 1, "Greenhouse": 1},
    }
    assert [row["open_roles"] for row in summaries["2026-10-05"]["trend"]] == [2, 3]


def test_headers_for_both_key_styles():
    new_style = sync.headers("sb_secret_abc")
    assert new_style["apikey"] == "sb_secret_abc"
    assert "Authorization" not in new_style
    legacy = sync.headers("eyJhbGciOi.payload.sig")
    assert legacy["Authorization"] == "Bearer eyJhbGciOi.payload.sig"


def test_base_url_accepts_the_data_api_address():
    assert sync.base_url("https://abc.supabase.co/rest/v1/") == "https://abc.supabase.co"
    assert sync.base_url("https://abc.supabase.co/") == "https://abc.supabase.co"
    assert sync.base_url(" https://abc.supabase.co ") == "https://abc.supabase.co"


def test_read_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "# comment\nSUPABASE_URL=https://x.supabase.co\n"
        "SUPABASE_SECRET_KEY='sb_secret_abc'\n\nBROKEN LINE\n"
    )
    assert sync.read_env_file(path) == {
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_SECRET_KEY": "sb_secret_abc",
    }
    assert sync.read_env_file(tmp_path / "missing.env") == {}


class _Response:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body or []
        self.text = ""

    def json(self):
        return self._body


class _FakeSession:
    """Pretends Supabase already has one job that the workbook dropped."""

    def __init__(self):
        self.deleted = []

    def get(self, url, params, headers, timeout):
        return _Response(body=[
            {"snapshot_date": "2026-10-05", "ats": "Ashby", "company_id": "A", "job_id": "a1"},
            {"snapshot_date": "2026-10-05", "ats": "Ashby", "company_id": "A", "job_id": "gone"},
        ])

    def delete(self, url, params, timeout):
        self.deleted.append(params)
        return _Response()


def test_prune_removes_rows_the_workbook_no_longer_has():
    session = _FakeSession()
    rows = [{"snapshot_date": "2026-10-05", "ats": "Ashby", "company_id": "A", "job_id": "a1"}]
    assert sync.prune(session, "https://x", "job_snapshots", rows) == 1
    assert session.deleted == [{
        "snapshot_date": "eq.2026-10-05", "ats": "eq.Ashby",
        "company_id": "eq.A", "job_id": "eq.gone",
    }]


def test_batches():
    assert [len(batch) for batch in sync.batches(list(range(1201)), 500)] == [500, 500, 201]
