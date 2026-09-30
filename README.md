# HiddenHire

Discover emerging job opportunities through candidate fit and company hiring momentum.

## Overview

HiddenHire is an MVP hiring-signal discovery platform. It helps job seekers find roles at emerging and lesser-known companies, instead of limiting a search to well-known employers or keyword matches alone.

A candidate enters target roles, skills, industries, and a preferred location. HiddenHire ranks current openings by how well each role fits that profile and by how the company’s hiring is changing over time. Each result links back to the original posting.

## The Problem

Job seekers often apply to companies they already know. Openings at emerging companies are harder to notice, especially when hiring activity is spread across many career sites. HiddenHire brings those openings together and ranks them using fit and recent hiring activity.

## How HiddenHire Works

Candidate Profile → Job Data Collection → Candidate Fit → Hiring Momentum → Hidden Opportunity Score → Opportunity Explanation → Original Job Posting

1. The candidate describes target roles, skills, industries, and location.
2. Job snapshots are collected from public company career boards.
3. Each opening is scored for candidate fit.
4. Each company is scored for hiring momentum from historical snapshots.
5. Fit and momentum are combined into a Hidden Opportunity score.
6. A short explanation states which of those signals support the result.
7. The card links to the original job posting.

## Core Features

- Candidate-to-job matching against the latest job snapshot
- Candidate Fit scoring
- Company Hiring Momentum from prior snapshots
- Hidden Opportunity ranking
- “Why this opportunity?” explanations based on the calculated signals
- Direct links to original job postings
- Historical job snapshots stored by date
- Automated weekly job-data collection

## Data Pipeline

Public job posts are collected from company boards on Ashby, Greenhouse, and Lever. Each run stores that day’s openings in `HiddenHire_Data.xlsx` and keeps earlier snapshot dates.

A GitHub Actions workflow runs the collectors in sequence, recalculates hiring momentum, and commits the updated workbook. It is scheduled for Monday morning New York time and can also be started manually. The company master list is not updated by the workflow.

## Scoring

Scores are rule-based. HiddenHire does not use an external language model.

**Candidate Fit** compares an opening with the profile:

- **Title (35%)**: 100 when the title contains a target role exactly, 75 for another title in the same role family.
- **Seniority (25%)**: the title is classified as entry, mid, or senior and scored against the experience level the candidate picks.
- **Skills (20%)**: the share of the candidate's skills found in the posting.
- **Industry (10%)**: full credit when the company is in any preferred industry.
- **Location (10%)**: full credit for the preferred location, partial credit for remote.

Skills, industries, roles, and seniority words match as whole words, so "Excel" does not match "excellent" and "intern" does not match "international". Results are limited to jobs in a target role family that meet the fit cutoff, leaving out titles two levels away from the chosen experience level.

**Hiring Momentum** is a company-level score. It compares the latest snapshot with the snapshot closest to seven days earlier: newly opened roles in the candidate's target role families (40%), the net change in those relevant roles (25%), the overall open-job growth rate (20%), and new postings overall (15%).

**Hidden Opportunity** ranks each job as 60% Candidate Fit and 40% Hiring Momentum.

The explanation under each result uses only signals those scores already support, such as role match, skills, industry, location, and whether hiring momentum is elevated, steady, or quieter.

## Tech Stack

- Python 3.11+
- Pandas
- Streamlit
- Excel workbooks via OpenPyXL
- Requests for public job-board APIs
- GitHub Actions for the weekly update
- pytest for the scoring tests

## Running the Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## MVP Status

HiddenHire is an independently developed MVP and portfolio project. It is actively being developed.

## Live Demo

[Try HiddenHire Live](https://hiddenhire.streamlit.app/)

## Screenshot

![HiddenHire results](hiddenhire-results.png)

## Future Development

- Highlight roles that newly appear between historical snapshots
- Collect from additional applicant-tracking systems
- Extend the hiring signals already calculated from snapshots
- Add international-student sponsorship signals

## Author

**Meng Han**  
M.S. Management and Analytics (Business Analytics), New York University
