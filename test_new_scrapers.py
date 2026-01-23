#!/usr/bin/env python3
"""
Simple test script for MyCareersFuture and JobsDB scrapers
"""
from jobspy import scrape_jobs

print("Testing MyCareersFuture scraper...")
print("="*60)
try:
    jobs_mcf = scrape_jobs(
        site_name=["mycareersfuture"],
        search_term="sustainability",
        location="Singapore",
        results_wanted=5,
        verbose=1
    )
    print(f"Found {len(jobs_mcf)} jobs from MyCareersFuture")
    if len(jobs_mcf) > 0:
        print("\nSample job:")
        print(jobs_mcf[['title', 'company', 'location', 'job_url']].head(1))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("Testing JobsDB scraper...")
print("="*60)
try:
    jobs_jobsdb = scrape_jobs(
        site_name=["jobsdb"],
        search_term="sustainability",
        location="Singapore",
        results_wanted=5,
        verbose=1
    )
    print(f"Found {len(jobs_jobsdb)} jobs from JobsDB")
    if len(jobs_jobsdb) > 0:
        print("\nSample job:")
        print(jobs_jobsdb[['title', 'company', 'location', 'job_url']].head(1))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("Test completed!")
