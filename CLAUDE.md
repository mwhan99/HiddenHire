# CLAUDE.md

Guide to the HiddenHire repository for Claude and for Meng (the owner).
Meng is new to web development. When working here, **explain each step in
plain English**: what you are about to do, why, and how to check it worked.

HiddenHire tracks the public job boards of 50 hand-picked New York
startups every week, then ranks openings for a job seeker by
**Candidate Fit** (how well a role matches them) and **Hiring Momentum**
(how fast the company is adding roles).

- Live site today: https://hiddenhire.streamlit.app/ (Streamlit, Python)
- Repo: https://github.com/mwhan99/HiddenHire
- Goal in progress: move the **website** to Next.js (App Router,
  TypeScript, Tailwind) on Vercel, with data in Supabase. The **Python
  scraper stays in Python.** See [Migration plan](#4-migration-plan).

Why the move, in Meng's words:
1. **It should look polished**, at the level of Meng's other project,
   Parrot (https://www.parrotaisearch.com/). That means a soft gradient
   background, a rounded floating nav bar, a big bold headline with a
   coloured accent word, small "chip" labels and roomy rounded cards.
   HiddenHire gets **its own colours and identity**, not a copy of
   Parrot's pink.
2. **It must never show "This app is asleep."** Recruiters click once and
   leave. The new site has to load in about a second on every visit,
   including the first one after a quiet week.

Numbers below were checked against the data on Oct 22, 2026.

---

## Working rules

- **The Streamlit site must stay up until the switch-over (step 11).**
  Meng is job hunting and the link is on applications. Until step 11:
  - Don't change `app.py`, `pipeline.py`, the scoring files,
    `requirements.txt` or the workbook's layout. Streamlit Cloud rebuilds
    the site from `main` on every push, and those are the files it runs.
  - New work goes in new files and folders (`web/`, `supabase/`,
    `supabase_sync.py`, `scripts/`), which Streamlit ignores.
  - Anything the Supabase sync needs goes in its own requirements file,
    not `requirements.txt`.
  - Work on a branch and merge with a pull request. After each merge,
    open https://hiddenhire.streamlit.app/ and check it still loads.
- Run the tests before and after any Python change:
  `pip install -r requirements-dev.txt` then `pytest` (52 tests today).
- **The search scoring exists twice**, in Python and in TypeScript
  (`web/lib/scoring/`). After any change to `candidate_fit.py`,
  `hiring_momentum.py`, `pipeline.py`, or `explain_opportunity` in
  `app.py`, run `python scripts/export_golden.py` using the
  `requirements.txt` package versions (pandas 3.0.6). Then run `npm test`
  in `web/` and update the TypeScript until it passes again. Commit the
  regenerated `config.json` and `golden.json.gz`.
- Never edit `HiddenHire_Data.xlsx` by hand in a commit. The weekly
  workflow rewrites it, and a merge conflict on a binary file can't be fixed by hand.
- The workflow fails on purpose if the **Companies** sheet changes during
  a run. The company list is changed by hand, on purpose, and nowhere else.
- Scoring numbers (weights, cutoffs, thresholds) appear in four places:
  the Python code, the README "Scoring" section, the Methodology tab in
  `app.py`, and `web/app/methodology/page.tsx`. Change all four together.
- Python 3.11+ is required (pandas 3.0.6 does not install on 3.10).
- Secrets (Supabase keys) go in GitHub Actions secrets / Vercel
  environment variables, never in the repo.

---

## 1. What each file does

### The website (Streamlit, to be replaced)

| File | What it does |
|---|---|
| `app.py` | The whole website. It shows a page title, a stats bar, four tabs (Find Opportunities, Company Momentum, Market Insights, Methodology), and a footer. It reads the workbook on page load and caches the results until the file changes. It holds the CSS, the "Why this opportunity?" sentence builder (`explain_opportunity`), the badge rules, and the Methodology text. |
| `.streamlit/config.toml` | Forces the light theme and sets the brand colours (`#0e4c5c` teal, `#f4f6f8` background, `#17212b` text). |

### The new website (Next.js, in progress)

| File | What it does |
|---|---|
| `web/` | The Next.js app (Next.js 16.4, React 19, Tailwind 4, TypeScript), live at https://hidden-hire.vercel.app. Vercel redeploys on every push to `main`. Run it locally with `npm run dev` inside `web/`, then open http://localhost:3000. Check it with `npm run lint` and `npm run build`. Don't run `npm run build` while `npm run dev` is running: they share `.next/` and the dev server breaks until restarted. |
| Design | Chosen in step 7: the **"Data briefing"** layout. A navy header (`bg-navy`) with a scrolling ticker of this week's changes, a left-aligned headline, then white cards of live data. Cobalt blue `brand` (#2563eb), green `up` for gains, Inter font. Colours are defined in `web/app/globals.css`. It deliberately avoids Parrot's look: no centred hero, floating pill nav, pastel blobs, gradient headline text or floating bubbles. |
| `web/app/page.tsx` | The home page: navy header, ticker, headline, the open-roles chart, growing-fastest companies, this week's new/closed roles, roles by function, and "How HiddenHire works". |
| `web/app/companies/` | Company Momentum. `page.tsx` is the leaderboard of every company in the latest snapshot, with a Growing / Steady / Slowing / New filter (`components/CompanyBoard.tsx`, the site's first browser-side "client" component). `[id]/page.tsx` is one page per company (e.g. `/companies/C016`), all prebuilt with `generateStaticParams`. It shows open roles, the week's change, a trend chart with peak and low, roles by function, and the week's new postings (first 10, then a toggle). "Size" always means open roles a week earlier (at least 10), never headcount. |
| `web/app/insights/page.tsx` | Market Insights ("This week's hiring briefing"). It has the week's headline numbers, **Key findings** (sentences generated from the data by `findings()`, so they stay correct each week), the open-roles trend, fastest-growing and slowing companies, and roles by function and industry (`components/BarList.tsx`). All of it is read from `market_summary` via `getLatestBriefing()`. |
| `web/app/methodology/page.tsx` | Methodology. Sections: how it works, coverage (live counts from `getCoverage()`), Candidate Fit weights and the seniority table, Hiring Momentum, ranking, Company Momentum labels, data quality fixes, limitations, and a "How it's built" pipeline diagram. There's a sticky table of contents on wide screens. The scoring numbers here are hand-written and must match the Python code. |
| `web/app/layout.tsx`, `web/app/not-found.tsx`, `web/app/icon.svg` | The frame around every page (font, page titles, footer); a styled "still being built" page for missing addresses; the browser-tab icon. |
| `web/components/` | Shared pieces: `SiteHeader` (menu, `NAV_LINKS`, highlights the current section), `PageHeader` (navy band for inner pages), `SiteFooter`, `Logo`, `Ticker`, `Card`, `MomentumBadge` (label colours and explanations), and `charts.tsx` (hand-drawn SVG `Sparkline` and `AreaChart`, no chart library). |
| `web/lib/format.ts` | Number and date display helpers (`fmt`, `signed`, `shortDate`, `longDate`, `nextMonday`). |
| `web/lib/scoring/` | The per-search scoring in TypeScript (migration step 8). `fit.ts` is Candidate Fit, `momentum.ts` is Hiring Momentum and the comparison dates, `rank.ts` combines them 60/40 and sorts, and `explain.ts` writes "Why this opportunity?" and the momentum badge. `match.ts` holds whole-word matching and role families, and `rounding.ts` copies Python's rounding (`round()` sends .5 to the even neighbour, pandas multiplies first, and quantile "nearest" rounds its position to even). `config.json` is **generated**, so don't edit it by hand. `scoring.test.ts` (run with `npm test`, Vitest 4) checks every result against Python's. |
| `scripts/export_golden.py` | Writes `web/lib/scoring/config.json` (role families, exclusions, seniority scores, family labels) and `__fixtures__/golden.json.gz`: 5 fixed searches with the exact Supabase-shaped inputs and Python's results, momentum per company, and explanation. It reads `explain_opportunity` from `app.py` without running Streamlit. |
| `web/lib/supabase.ts`, `web/lib/data.ts` | Read from Supabase with the read-only publishable key. Each data function uses `"use cache"` + `cacheLife("hours")`, so pages are prebuilt and refreshed about hourly. Settings: `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `web/.env.local` (git-ignored) and in Vercel. They have no `NEXT_PUBLIC_` prefix, so they stay on the server. |
| Monday timing | The Monday job commits the workbook *before* it syncs Supabase, so Vercel's rebuild can run a minute before the new data arrives. The site can then show last week's numbers for up to an hour, until the hourly refresh catches up. |
| `web/AGENTS.md` | Written by Next.js itself. **This Next.js version differs from older ones**, so read the matching guide in `web/node_modules/next/dist/docs/` before writing Next.js code. Cache Components and Partial Prefetching are switched on in `web/next.config.ts`. |

### Scoring and analysis (pure Python, no web code)

| File | What it does |
|---|---|
| `pipeline.py` | `rank_hidden_opportunities(...)` is the function the search form calls. It loads the workbook, drops inactive companies, scores the latest snapshot's jobs for fit, scores companies for momentum, combines them (60/40) and sorts the results. It also has `is_active()`. |
| `candidate_fit.py` | The Candidate Fit score. It holds the role families, the excluded titles, the seniority words, the whole-word matcher `contains_term`, and `score_candidate_fit`. Run it as a script (`python candidate_fit.py`) and it scores a built-in test profile and writes the **Candidate_Fit** sheet. |
| `hiring_momentum.py` | The Hiring Momentum score: `calculate_hiring_momentum`, `choose_comparison_dates`, `size_adjusted` and `normalize_signal`. Run as a script (the workflow does this), it writes the **Hiring_Baseline** sheet and prints a long audit report. |
| `market_insights.py` | Numbers that don't depend on the searcher. These are the headline counts, company movers, the Company Momentum leaderboard (Growing / Steady / Slowing / New to tracking), roles by job function and by industry, and trend lines. It also holds `classify_function` (the keyword rules that turn job titles into functions). |
| `opportunity_score.py` | An older script from before `pipeline.py`. It reads the **Candidate_Fit** sheet and writes **Hidden_Opportunities**. **The app and the workflow don't use it.** |

### The scraper (stays in Python)

| File | What it does |
|---|---|
| `ashby_collector.py` | Fetches every active Ashby company's jobs from `api.ashbyhq.com/posting-api/job-board/<slug>`. It then replaces today's Ashby rows in **Job_Snapshots**. |
| `greenhouse_collector.py` | The same for Greenhouse (`boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true`). It turns the escaped HTML descriptions into plain text. |
| `lever_collector.py` | The same for Lever (`api.lever.co/v0/postings/<slug>?mode=json`). It joins the intro, the bullet lists and the closing text into one description. |
| `gem_collector.py` | An unfinished experiment for reading Gem job boards. It imports `bs4`, which is not in `requirements.txt`. **Nothing uses it.** |
| `.github/workflows/weekly-data-update.yml` | Runs the collectors every Monday and commits the updated workbook (see section 2). |
| `supabase_sync.py` | Copies the workbook into Supabase (migration step 3). It reuses the existing Python scoring code to add job labels and to precalculate Company Momentum and Market Insights for every snapshot date. `--dry-run` builds everything without sending. It reads `SUPABASE_URL` and `SUPABASE_SECRET_KEY` from the environment or `.env`. |
| `.github/workflows/supabase.yml` | "Run workflow" re-syncs the current workbook to Supabase without scraping. It also reads one row every day so the free Supabase project never pauses. |
| `supabase/schema.sql` | The Supabase tables, plus the rules that make them read-only for the website (migration step 2). Safe to run again. |

### Data, tests and docs

| File | What it does |
|---|---|
| `HiddenHire_Data.xlsx` | **The database today** (about 8.5 MB). Its sheets are described in section 2. |
| `tests/` | pytest tests. `conftest.py` lets the tests import the root modules. There are test files for candidate fit, hiring momentum, market insights and the pipeline. Each data-quality fix in the README has a test. |
| `requirements.txt` / `requirements-dev.txt` | Python packages: streamlit, pandas, openpyxl and requests, plus pytest for development. |
| `README.md` | The public project write-up, with the scoring explanation, limitations and screenshots. |
| `hiddenhire-results.png`, `hiddenhire-company-momentum.png` | README screenshots. |
| `.gitignore` | Ignores caches, `.env`, virtual environments and Excel lock files (`~$*.xlsx`). |

---

## 2. Where the data comes from

### The company list

Meng hand-picked 50 venture-backed NYC startups in September 2026, from
StartupsGallery, TopStartups and Y Combinator's directory. They live in
the **Companies** sheet:

`Company_ID` (C001…), `Company_Name`, `Industry` (tags split by " / ",
e.g. "AI / FinTech / SaaS"), `Location`, `Company_Size`, `Company_Stage`,
`Company_Website`, `Careers_URL`, `ATS`, `ATS_Identifier`, `Source`,
`Date_Added`, `Active`.

- An **ATS** (applicant tracking system) is the service that hosts a
  company's job board. Of the 50 companies, 31 use Ashby, 11 Greenhouse,
  3 Gem, 2 Comeet, 2 Lever and 1 Dover.
- **43 are Active**: the ones on Ashby, Greenhouse or Lever, which have a
  collector. Among the active ones, Ashby has 30, because one Ashby
  company is marked inactive.
- Inactive companies are skipped by the collectors and hidden from every
  score.
- The board "slug" comes from `ATS_Identifier`. If that is blank, the
  Ashby and Greenhouse collectors take it from `Careers_URL`. Lever needs
  `ATS_Identifier`.

### The workbook's sheets

| Sheet | Rows | Written by | Read by the website? |
|---|---|---|---|
| Companies | 50 | Meng, by hand | Yes |
| Job_Snapshots | 8,585 | the three collectors | **Yes, this is the main data** |
| Hiring_Baseline | 43 | `hiring_momentum.py` (weekly) | No |
| Candidate_Fit | 36 | `candidate_fit.py` (manual run) | No |
| Hidden_Opportunities | 36 | `opportunity_score.py` (manual run) | No |

**Job_Snapshots** has one row per job per snapshot date:
`Snapshot_Date`, `Company_ID`, `Company_Name`, `Job_ID`, `Job_Title`,
`Department`, `Location`, `Employment_Type`, `Date_Posted`, `Job_URL`,
`Job_Description`, `ATS`.

- A job that stays open for five weeks appears five times, once per date.
- The same row is identified by (date, ATS, company, Job_ID).
- The snapshot dates are 2026-09-20, 09-27, 09-28, 09-30, 10-05, 10-12
  and 10-19. Each has about 1,200–1,260 jobs. Sept 28 and 30 were extra
  manual runs.
- Descriptions add up to about 43 million characters. Because each job is
  stored once per week, the same text is repeated every week.

### How the weekly scrape works

`.github/workflows/weekly-data-update.yml`, step by step:

1. **When.** GitHub schedules run on UTC time, so there are two Monday
   crons: 12:00 and 13:00 UTC. A small "gate" job keeps whichever one is
   8:00 AM in New York that week (daylight vs standard time). A manual
   run ("Run workflow" button, `workflow_dispatch`) always goes ahead.
2. **Setup.** Check out `main`, install Python 3.11 and the packages, and
   save a copy of the Companies sheet.
3. **Collect.** Run `ashby_collector.py`, then `greenhouse_collector.py`,
   then `lever_collector.py`. Each one:
   - fetches every active company on its ATS;
   - **if any company fails to download, exits with an error and saves
     nothing**, so a half-finished week never gets saved;
   - otherwise deletes *today's* rows for its own ATS (so running twice
     in a day doesn't create duplicates), adds the fresh rows, and
     rewrites the Job_Snapshots sheet.
4. **Recalculate.** `python hiring_momentum.py` rewrites Hiring_Baseline
   and prints the momentum audit to the log.
5. **Validate.** The run fails if any of these happen:
   - the workbook is missing;
   - the Companies sheet changed;
   - there are no rows for today;
   - any (date, ATS, company, Job_ID) appears twice.
6. **Commit.** The bot commits `HiddenHire_Data.xlsx` to `main`, with a
   message like "Weekly HiddenHire data update 2026-10-19".

Streamlit Cloud sees the new commit and redeploys. `app.py` caches its
tables based on the workbook's last-changed time, so the next visitor
gets fresh numbers.

If any step fails, the later steps don't run and nothing is committed.
The fix is to look at the log in the GitHub Actions tab and re-run.

---

## 3. How the scores are calculated

All scores are plain rules. No AI model is involved.

**Whole-word matching** (`contains_term`). A word only counts if it is
not part of a longer word. "excel" does not match "excellent", "ai" does
not match "supply chain", and "intern" does not match "international".
Phrases with spaces or symbols like "fp&a" and "head of" still work.
Upper/lower case is ignored.

### 3a. Candidate Fit (0–100, one per job)

The searcher gives:
- target roles (picked from a fixed list);
- an experience level (entry, mid or senior);
- skills, typed with commas between them;
- preferred industries, typed with commas between them;
- a location.

**Role families.** There are 8 groups of related titles in
`ROLE_FAMILIES`: business analytics, strategy, operations, finance,
marketing/growth, product, software engineering and data science/ML.
Picking "business analyst" brings in its whole family: data analyst,
business intelligence, and so on.

Titles containing "people operations", "legal operations", "workplace
operations" and similar (`ROLE_EXCLUSIONS`) never count as a match.

Each job gets five sub-scores, then a weighted average:

| Part | Weight | Rule |
|---|---|---|
| Title | 35% | 100 if the title contains one of the exact target roles. 75 if it only matches another title in the same family. |
| Seniority | 25% | The title is labelled senior, entry, mid or unknown. The first match wins, checked in that order. **Senior** words: senior, sr, staff, principal, lead, head of, director, VP, chief. **Entry** words: intern, new grad, junior, analyst, associate, coordinator, specialist and similar. **Mid** words: manager, II, III. "Member of Technical Staff" is not treated as senior. The label is then scored against the searcher's level using the table below. |
| Skills | 20% | The share of the searcher's skills found in the description, rounded. For example, 3 of 4 gives 75. A job with no description gets 0. |
| Industry | 10% | 100 if the company's industry contains *any* preferred industry, else 0. |
| Location | 10% | 100 if the job location contains the preferred location ("New York" also accepts "NYC"). 75 if it says "remote". Else 0. This check is plain text, not whole-word. |

Seniority table (row = searcher's level, column = the title's level):

| | entry | mid | senior | unknown |
|---|---|---|---|---|
| entry | 100 | 40 | 0 | 50 |
| mid | 50 | 100 | 40 | 50 |
| senior | 0 | 50 | 100 | 50 |

`Candidate_Fit_Score = 0.35·Title + 0.25·Seniority + 0.20·Skills + 0.10·Industry + 0.10·Location`, rounded to 1 decimal.

**Which jobs appear.** A job is shown only if it passes all three checks:
- it matches one of the searcher's role families;
- its seniority sub-score is above 0 (so no Director roles for an entry
  search);
- its fit is **at least 40**.

Only the **latest** snapshot's jobs are scored.

Example: an entry-level searcher with skills SQL, Excel, Tableau and
Python, looking for fintech in New York, sees "Business Analyst" at a
fintech in NYC whose posting mentions 3 of the 4 skills:
35 + 25 + 15 + 10 + 10 = **95**.

### 3b. Hiring Momentum (0–100, one per company, *depends on the search*)

1. **Pick two dates.**
   - "Now" is the latest snapshot.
   - "Before" is the snapshot closest to 7 days earlier, but at least 5
     days earlier. If two are equally close, the later one wins.
   - If no snapshot is 5+ days older yet, use the one just before "now".
2. **Count per company.** Jobs are matched by (company, Job_ID).
   - open roles before and now;
   - **new** roles (open now, not before);
   - **closed** roles (open before, not now);
   - the same counts for **relevant** roles only, meaning titles in the
     searcher's role families. This is why momentum changes with the
     search.
3. **Make four signals and adjust for size.** Each count is divided by
   the company's open roles *before*, with a minimum of 10. So 5 new roles
   at a 15-job startup count more than 5 new roles at a 150-job company.
   - new relevant roles
   - net relevant change (new relevant − closed relevant)
   - overall growth (open now − open before)
   - new roles overall
4. **Newly tracked companies.** A company with 0 roles before was probably
   just added to the list, so all four of its signals are set to 0,
   which ends up as a neutral 50.
5. **Scale each signal to 0–100** across all active companies:
   - Take the 90th-percentile size of the non-zero values. pandas
     "nearest" rule: pick a real value, don't average two.
   - Score = 50 + 50 × (value ÷ that number), kept between 0 and 100.
   - So no change = 50, growth goes toward 100 and shrinking goes toward 0.
   - If every company is 0, everyone gets 50.
   - Because of this step, **one company's score depends on every other
     company**.
6. `Hiring_Momentum_Score = 0.40·new relevant + 0.25·net relevant + 0.20·overall growth + 0.15·new overall`, rounded to 1 decimal.

The result badge reads "▲ Hiring fast" at 60 or more, "● Steady hiring"
from 45 up to 60, and "▼ Quieter hiring" below 45.

### 3c. Opportunity score and ranking

`Hidden_Opportunity_Score = 0.60 · Fit + 0.40 · Momentum`, rounded to 1 decimal.

- Results are sorted by Opportunity, then Fit, then company name, then
  title.
- The page shows one card per company (its best job), with the company's
  other matches in a "N more matching roles" dropdown.
- "Why this opportunity?" is built only from sub-scores that are actually
  high: an exact role or family, a matched industry, some or all skills,
  the location or remote, and the momentum band.

### 3d. Company Momentum leaderboard (the same for every visitor)

This uses the same two dates and the same size adjustment, but counts all
roles, not just relevant ones.

- `Growth_Rate = (open now − open before) ÷ max(open before, 10)`
- **Growing** if the rate is +0.05 or more, **Slowing** if −0.05 or
  less, and **Steady** in between.
- **New to tracking** if the company had 0 roles before.
- Sorted by Growth_Rate, highest first.
- The stats bar's "Biggest jump" is different: it is the largest *raw*
  increase in roles, so it can name a different company.

Market Insights also shows week-over-week totals, the fastest-growing
and slowing companies, roles by job function (`classify_function`
keyword rules), roles by industry tag (a company with 3 tags counts
toward all 3) and open roles over time.

---

## 4. Migration plan

**Goal:** the website moves to Next.js on Vercel and reads from Supabase.
The **scraper stays in Python** on GitHub Actions. Streamlit stays live
until the new site matches it, so there is never a broken public demo.

### The main design decision (please review)

The tricky part is that some scores can be calculated ahead of time and
some can't:

- **The same for everyone:** stats bar, Company Momentum, Market Insights
  and Methodology numbers. → **Python calculates these once a week** and
  saves the answers to Supabase. The website just displays them. This
  keeps the existing, tested Python code in charge.
- **Different for each search:** Candidate Fit, plus Hiring Momentum,
  because "relevant roles" depend on the chosen roles. Skills and
  industries are typed freely, so these can't be calculated ahead of
  time. → They must run **when someone clicks Search**.

**Recommended:** re-write *only the per-search scoring* in TypeScript,
inside Next.js. That is fit, momentum and the 60/40 combination, roughly
300 lines.

To keep it small and safe, Python saves helper columns on every job each
week:
- `role_families`: which families the title belongs to, with exclusions
  already applied;
- `seniority`: entry, mid, senior or unknown;
- `job_function`.

The TypeScript side then only has to do:
- the whole-word matches for target roles, skills and industries;
- the location check;
- the count-and-scale momentum math.

Then a **"golden" test** checks that the TypeScript version gives the same
answers as Python. A Python script saves the Python results for a few
fixed searches to a JSON file, and the TypeScript tests must reproduce
them.

*Rejected alternatives:*
- Running the Python scoring on Vercel. Vercel's Python functions have
  size limits that pandas makes tight, and mixing two languages in one
  deploy is harder to debug.
- Moving the scoring into Supabase as SQL. That is harder for a beginner
  to read and test.

### Proposed Supabase tables

| Table | One row per | Filled by |
|---|---|---|
| `companies` | company (the same columns as the sheet) | sync script |
| `job_snapshots` | job × snapshot date: the sheet's columns minus the description, plus `role_families text[]`, `seniority`, `job_function` | sync script |
| `job_descriptions` | job (company_id, job_id), latest text | sync script |
| `company_momentum` | company × snapshot date: open now, change, new, closed, growth rate, label, trend (array) | sync script, using `market_insights.company_momentum` |
| `market_summary` | snapshot date: headline numbers, functions, industries, trend, coverage (stored as JSON) | sync script |

Descriptions get their own table so the same text isn't stored once per
week. Today that would be about 43 MB, growing by about 7 MB a week; on
its own table it stays around 7–10 MB. Supabase's free tier allows 500 MB.

**Keeping Supabase awake.** Free Supabase projects are *paused* after
about a week without any activity. The Monday sync is cutting it close.
So:
- add a tiny daily "ping" (a scheduled GitHub Action, or a Vercel Cron
  job, that reads one row);
- the cached pages above keep showing even if the database is briefly
  unreachable.

**Security.** The website uses the public **publishable** key
(`sb_publishable_...`, called "anon" in older projects), with Row Level
Security set to *read-only*. Only the GitHub Action and
`supabase_sync.py` use the **secret** key (`sb_secret_...`, called
"service_role" in older projects), which can write. The secret key must
**never** get a `NEXT_PUBLIC_` name or be used in browser code.

### Steps

Each step ends with a check. Don't start the next step until it passes.

**Phase A — get the data into Supabase (Python only, the website is unchanged)**

1. **Create the accounts.** Supabase (a free project) and Vercel (log in
   with GitHub). Install Node.js LTS on the Mac.
   *Check:* `node -v` prints a version.
2. **Create the tables.** Add a `supabase/schema.sql` file to the repo,
   with the tables above and read-only policies, and run it in the
   Supabase SQL editor. *Check:* the tables show up in the Table Editor.
3. **Write `supabase_sync.py`.** It reads the workbook and fills
   everything in using the *existing* Python functions:
   - `classify_seniority`, `calculate_family_match` and
     `classify_function` for the helper columns;
   - `company_momentum`, `headline` and the rest of `market_insights.py`
     for the summaries.

   It "upserts" (insert, or update if the row already exists), so
   running it twice is safe. Add tests for its data-shaping functions.
   *Check:* run it locally once to load all past snapshots. Each date's
   row count in Supabase must match the workbook, for example 1,259 on
   10-19.
4. **Add the sync to the weekly workflow.** It goes as the **last** step,
   *after* "Commit the workbook", with `SUPABASE_URL` and
   `SUPABASE_SECRET_KEY` saved as GitHub secrets. Because it comes
   last, a Supabase problem can never stop the spreadsheet update the
   Streamlit site depends on. The Excel commit stays exactly as it is, so
   for now the data goes to both places. *Check:* click "Run workflow" by hand.
   It should pass, and Supabase should show today's date.

**Phase B — build the read-only pages (no scoring yet)**

5. **Create the app.** In a `web/` folder in this same repo, run
   `npx create-next-app@latest web --typescript --tailwind --app --eslint`.
   One repo keeps the scraper, the docs and the site together.
   *Check:* `npm run dev` inside `web/` shows the starter page at
   localhost:3000.
6. **Connect to Supabase.** Install `@supabase/supabase-js` and put the
   URL and publishable key in `web/.env.local`, which is git-ignored. Then
   connect Vercel: import the repo, set Root Directory = `web`, and add
   the same two variables. *Check:* a test page lists the company names,
   locally and on the Vercel preview link.
7. **Build the parts that don't depend on a search.** These are the page
   title, the stats bar, Company Momentum (table, filter, company detail,
   trend charts), Market Insights, Methodology and the footer. Data
   loading should happen on the server: these are "Server Components" in
   Next.js, which run before the page reaches the browser. Use a small
   chart library such as Recharts.

   **Design.** Start with a short design pass: agree on a colour palette,
   a font and a hero section with Meng before building the pages. Use the
   Parrot-style layout described at the top of this file, with
   HiddenHire's own colours.

   **No waiting.** Use Next.js caching ("revalidate"). Vercel builds each
   page ahead of time and refreshes it in the background about once an
   hour, so visitors get a ready-made page instantly instead of waiting
   for a database call. *Check:* each number matches the Streamlit
   site for the same week.

**Phase C — the search (the risky part)**

8. **Re-write the per-search scoring in TypeScript** (done, see `web/lib/scoring/`), in
   `web/lib/scoring/`:
   - `contains_term`. JavaScript regex supports the same "not part of a
     longer word" check.
   - the role-family list. Generate it from Python into a JSON file so
     the two can't disagree, instead of copying it by hand.
   - the seniority table, the fit formula and `choose_comparison_dates`;
   - the momentum signals and the scaling, including pandas' "nearest"
     90th-percentile rule;
   - the 60/40 combination;
   - `explain_opportunity`.

   Add `scripts/export_golden.py`, which saves Python's
   `rank_hidden_opportunities` output for 4–5 fixed searches. Then add
   Vitest tests that compare against it, allowing a difference of 0.1.
   *Check:* the tests pass. Watch out for rounding: Python rounds .5 to
   the nearest even number, JavaScript always rounds .5 up.
9. **Build the search form and result cards.** The form is a "Client
   Component" (interactive, runs in the browser). It sends the search to
   a "Server Action" (runs on Vercel), which loads the latest and
   comparison snapshots from Supabase, scores them and returns the
   results. Only fetch descriptions for jobs whose `role_families` match
   the search: 43 jobs for the default search on 10-19, and 242 even
   with every family picked. *Check:* the default search
   gives the same companies, order and scores as Streamlit.

**Phase D — switch over**

10. **Polish.** Phone width, page titles and link previews, a loading
    state for the search, and an error message if Supabase is down.
    Optionally, buy a custom domain (about $10–15 a year) and connect it
    in Vercel. Otherwise the free address is `<name>.vercel.app`.
    *Check:* test on a real phone. Open the link in a private window
    after a few days with no visitors: it should load in about a second.
11. **Switch over.** Point the README and résumé links at the Vercel URL
    and refresh the screenshots. Keep the Streamlit app running as a
    backup for as long as old applications might still be read; it costs
    nothing. When it is finally retired, replace it with a short page
    linking to the new site, so old links never show an error.
12. **Later (optional).** Once the new site has been stable for a while:
    - have the collectors write straight to Supabase and stop committing
      the Excel file each week;
    - delete `app.py`, `opportunity_score.py`, `gem_collector.py` and the
      unused sheets, and drop `streamlit` from `requirements.txt`;
    - decide whether the Python scoring code stays only to produce the
      golden test files.

### Decisions for Meng

1. Is it OK to re-write the per-search scoring in TypeScript and check it
   with golden tests? (Recommended. The other options are above.)
2. Should the site live in a `web/` folder in this repo, or a separate
   repo? (Recommended: `web/` in this repo.)
3. Should descriptions go in their own table instead of being repeated
   every week? (Recommended: yes.)
4. Should Excel stay as the main data source until step 12? (Recommended:
   yes, so the working pipeline isn't touched while the site is being
   built.)
