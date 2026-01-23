#!/usr/bin/env python3
"""
Direct test of scrapers without pandas dependency
"""
import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scrapers directly from their modules (bypassing jobspy/__init__.py)
from jobspy.mcareersfuture.__init__ import MyCareersFuture
from jobspy.jobsdb.__init__ import JobsDB
from jobspy.model import ScraperInput, Country, DescriptionFormat

print("="*80)
print("Testing MyCareersFuture Scraper")
print("="*80)

try:
    mcf = MyCareersFuture()
    
    scraper_input = ScraperInput(
        site_type=[mcf.site],
        search_term="sustainability",
        location="Singapore",
        results_wanted=5,
        hours_old=168,  # Last 7 days
        description_format=DescriptionFormat.HTML
    )
    
    print(f"Searching for: {scraper_input.search_term}")
    print(f"Location: {scraper_input.location}")
    print(f"Results wanted: {scraper_input.results_wanted}\n")
    
    response = mcf.scrape(scraper_input)
    jobs = response.jobs
    
    print(f"Found {len(jobs)} jobs from MyCareersFuture\n")
    
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title}")
        print(f"   Company: {job.company_name}")
        print(f"   Location: {job.location.display_location() if job.location else 'N/A'}")
        print(f"   Posted: {job.date_posted}")
        print(f"   URL: {job.job_url}")
        if job.compensation:
            print(f"   Salary: {job.compensation.min_amount}-{job.compensation.max_amount} {job.compensation.currency}/{job.compensation.interval.value if job.compensation.interval else 'N/A'}")
        if job.description:
            desc_preview = job.description[:150].replace('\n', ' ') if job.description else ""
            print(f"   Description: {desc_preview}...")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Testing JobsDB Scraper")
print("="*80)

try:
    jobsdb = JobsDB()
    
    scraper_input = ScraperInput(
        site_type=[jobsdb.site],
        search_term="sustainability",
        location="Singapore",
        results_wanted=5,
        hours_old=168,
        description_format=DescriptionFormat.HTML
    )
    
    print(f"Searching for: {scraper_input.search_term}")
    print(f"Location: {scraper_input.location}")
    print(f"Results wanted: {scraper_input.results_wanted}\n")
    
    response = jobsdb.scrape(scraper_input)
    jobs = response.jobs
    
    print(f"Found {len(jobs)} jobs from JobsDB\n")
    
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.title}")
        print(f"   Company: {job.company_name}")
        print(f"   Location: {job.location.display_location() if job.location else 'N/A'}")
        print(f"   Posted: {job.date_posted}")
        print(f"   URL: {job.job_url}")
        if job.description:
            desc_preview = job.description[:150].replace('\n', ' ') if job.description else ""
            print(f"   Description: {desc_preview}...")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Test completed!")
print("="*80)
