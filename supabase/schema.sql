-- HiddenHire database tables for Supabase.
--
-- How to use: open the Supabase dashboard -> SQL Editor -> New query,
-- paste this whole file, and click Run. It is safe to run again: it only
-- creates what is missing and resets the read-only rules.
--
-- Who can do what:
--   * The website uses the public "anon" key and can only READ.
--   * The weekly GitHub Action uses the secret "service_role" key, which
--     skips these rules, so it is the only thing that can WRITE.
--
-- The Python scripts fill every table. Nothing here is typed in by hand.

begin;

-- ------------------------------------------------------------------
-- companies: the hand-picked company list (the "Companies" sheet).
-- ------------------------------------------------------------------
create table if not exists public.companies (
    company_id      text primary key,          -- C001, C002, ...
    company_name    text not null,
    industry        text,                       -- tags split by " / "
    location        text,
    company_size    text,                       -- e.g. 11-50
    company_stage   text,                       -- e.g. Series A
    company_website text,
    careers_url     text,
    ats             text,                       -- Ashby, Greenhouse, Lever, ...
    ats_identifier  text,
    source          text,
    date_added      date,
    active          boolean not null default true,
    updated_at      timestamptz not null default now()
);

-- ------------------------------------------------------------------
-- job_snapshots: one row per job per weekly snapshot (the
-- "Job_Snapshots" sheet, minus the long description text).
-- The last three columns are worked out by Python so the website
-- does not have to repeat that logic.
-- ------------------------------------------------------------------
create table if not exists public.job_snapshots (
    snapshot_date   date not null,
    ats             text not null,
    company_id      text not null references public.companies (company_id),
    job_id          text not null,              -- stored as text: Greenhouse IDs are numbers, others are not
    company_name    text,
    job_title       text,
    department      text,
    location        text,
    employment_type text,
    date_posted     timestamptz,
    job_url         text,
    role_families   text[] not null default '{}',   -- e.g. {business_analytics,strategy}
    seniority       text not null default 'unknown'
                    check (seniority in ('entry', 'mid', 'senior', 'unknown')),
    job_function    text,                       -- e.g. "Data & Analytics"
    primary key (snapshot_date, ats, company_id, job_id)
);

create index if not exists job_snapshots_date_idx
    on public.job_snapshots (snapshot_date);
create index if not exists job_snapshots_company_date_idx
    on public.job_snapshots (company_id, snapshot_date);
create index if not exists job_snapshots_role_families_idx
    on public.job_snapshots using gin (role_families);

-- ------------------------------------------------------------------
-- job_descriptions: the latest description for each job, stored once
-- instead of once per week. Only needed for the skills part of
-- Candidate Fit.
-- ------------------------------------------------------------------
create table if not exists public.job_descriptions (
    company_id  text not null references public.companies (company_id),
    job_id      text not null,
    description text,
    last_seen   date not null,                  -- latest snapshot that had this job
    primary key (company_id, job_id)
);

-- ------------------------------------------------------------------
-- company_momentum: the Company Momentum leaderboard, saved once per
-- snapshot date (market_insights.company_momentum in Python).
-- ------------------------------------------------------------------
create table if not exists public.company_momentum (
    snapshot_date date not null,
    company_id    text not null references public.companies (company_id),
    company_name  text not null,
    open_now      integer not null,
    net_change    integer,                      -- empty when "New to tracking"
    new_roles     integer,
    closed_roles  integer,
    growth_rate   double precision,             -- net change / max(open before, 10)
    momentum      text not null
                  check (momentum in ('Growing', 'Steady', 'Slowing', 'New to tracking')),
    rank          integer not null,             -- 1 = top of the leaderboard
    trend         integer[] not null,           -- open roles at each snapshot, oldest first
    functions     jsonb not null default '[]',  -- [{"function": ..., "open_now": ...}]
    new_postings  jsonb not null default '[]',  -- [{"job_title": ..., "location": ..., "job_url": ...}]
    primary key (snapshot_date, company_id)
);

-- ------------------------------------------------------------------
-- market_summary: everything else on the page that is the same for
-- every visitor (stats bar, Market Insights, Methodology numbers),
-- one row per snapshot date.
-- ------------------------------------------------------------------
create table if not exists public.market_summary (
    snapshot_date date primary key,
    headline      jsonb not null,               -- open, new, closed roles, growing/slowing counts, ...
    growing       jsonb not null default '[]',  -- fastest-growing companies
    slowing       jsonb not null default '[]',
    functions     jsonb not null default '[]',  -- open roles by job function
    industries    jsonb not null default '[]',  -- open roles by industry tag
    trend         jsonb not null default '[]',  -- open roles at each snapshot
    coverage      jsonb not null default '{}',  -- curated / active / per-ATS counts
    updated_at    timestamptz not null default now()
);

-- ------------------------------------------------------------------
-- Read-only access for the website.
-- Row Level Security (RLS) blocks everything unless a policy allows it.
-- Each table gets one policy: anyone may SELECT (read). There are no
-- insert/update/delete policies, so the public key cannot change data.
-- ------------------------------------------------------------------
do $$
declare
    t text;
begin
    foreach t in array array[
        'companies', 'job_snapshots', 'job_descriptions',
        'company_momentum', 'market_summary'
    ]
    loop
        execute format('alter table public.%I enable row level security', t);
        execute format('drop policy if exists "Public read" on public.%I', t);
        execute format(
            'create policy "Public read" on public.%I for select to anon, authenticated using (true)',
            t
        );
        execute format('revoke insert, update, delete, truncate on public.%I from anon, authenticated', t);
        execute format('grant select on public.%I to anon, authenticated', t);
    end loop;
end
$$;

commit;
