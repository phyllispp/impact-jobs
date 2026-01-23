import csv
from jobspy import scrape_jobs

# Search for CORE impact-related jobs in Singapore posted since yesterday
# Targeting specific impact job titles and roles
search_query = (
    '"impact manager" OR "impact analyst" OR "impact officer" OR "impact investing" '
    'OR "social impact manager" OR "social impact analyst" OR "ESG manager" OR "ESG analyst" '
    'OR "sustainability manager" OR "sustainability director" OR "sustainability officer" '
    'OR "CSR manager" OR "corporate social responsibility" OR "sustainable finance" '
    'OR "green finance" OR "responsible investment" OR "impact measurement" '
    'OR "climate risk analyst" OR "climate analyst" OR "environmental manager" '
    'OR "B Corp" OR "social enterprise" OR "impact fund"'
)

jobs = scrape_jobs(
    site_name=["indeed"],
    search_term=search_query,
    location="Singapore",
    country_indeed="Singapore",
    hours_old=24,  # Since yesterday (24 hours)
    results_wanted=50,  # Get up to 50 results
    verbose=2,  # Show all logs
)

print(f"\nFound {len(jobs)} jobs")
print("\n" + "="*80)
print("Job Results:")
print("="*80)

if len(jobs) > 0:
    print(jobs.head())
    print("\n" + "="*80)
    print(f"Total jobs found: {len(jobs)}")
    print("="*80)
    
    # Save to CSV
    jobs.to_csv("indeed_singapore_impact_jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    print("\nResults saved to 'indeed_singapore_impact_jobs.csv'")
else:
    print("No jobs found matching the criteria.")
