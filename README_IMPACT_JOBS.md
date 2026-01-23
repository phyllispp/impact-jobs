# Core Impact Jobs Search - Singapore

A tool to search for core impact-related jobs in Singapore across Indeed, LinkedIn, and Google.

## Features

- 🔍 Searches across multiple job sites (Indeed, LinkedIn, Google)
- 🎯 Advanced filtering to find genuine impact roles
- 📅 Jobs from the last 7 days
- 🌐 Beautiful web interface to view jobs
- ✅ Filters out false positives (generic engineering, insurance, etc.)

## Quick Start

### 1. Search for Jobs

Run the search script to find impact jobs:

```bash
python search_core_impact_jobs.py
```

This will:
- Search across Indeed, LinkedIn, and Google
- Filter for core impact roles
- Save results to `singapore_core_impact_jobs.csv`
- Automatically generate `index.html` website

### 2. View Jobs in Web Interface

After running the search, open `index.html` in your web browser:

```bash
open index.html  # macOS
# or just double-click index.html
```

The web interface shows:
- Job title
- Company name
- Post date
- Source site (LinkedIn/Indeed/Google badge)
- Direct link to apply

### 3. Regenerate Website (if needed)

If you want to regenerate the website from an existing CSV:

```bash
python generate_job_website.py
```

## What Jobs Are Included?

The search looks for roles with impact-related keywords in titles or descriptions:

- **Impact roles**: Impact Manager, Impact Analyst, Impact Investing
- **ESG roles**: ESG Manager, ESG Analyst, ESG Consultant
- **Sustainability roles**: Sustainability Manager, Sustainability Director
- **Climate roles**: Climate Analyst, Climate Risk Manager
- **Environmental roles**: Environmental Manager, Environmental & Social roles
- **Sustainable Finance**: Green Finance, Responsible Investment

## Filtering

The script intelligently filters out:
- ❌ Generic engineering roles (unless explicitly environmental/sustainability focused)
- ❌ Insurance/underwriting roles (unless ESG-focused)
- ❌ Roles where "impact" is just generic business language
- ❌ Roles where CSR/sustainability is only mentioned as company benefits
- ❌ Legal/Finance roles where sustainability is peripheral

## Output Files

- `singapore_core_impact_jobs.csv` - All job data in CSV format
- `index.html` - Beautiful web interface to view jobs

## Requirements

- Python 3.10+
- JobSpy library (installed via pip)
- Dependencies: pandas, requests, beautifulsoup4, etc.

## Notes

- LinkedIn may have rate limiting if you run searches too frequently
- Google Jobs requires very specific search syntax and may not always return results
- The search looks for jobs posted in the last 7 days (168 hours)

## Example Output

The web interface displays jobs in a card-based layout with:
- Gradient purple header
- Statistics showing total jobs and breakdown by site
- Responsive grid layout
- Hover effects on job cards
- Direct links to job postings

Enjoy finding your next impact role! 🌱
