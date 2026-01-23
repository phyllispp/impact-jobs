#!/usr/bin/env python3
"""
Quick test of MyCareersFuture scraper
"""
import sys
from jobspy import scrape_jobs

print("Testing MyCareersFuture scraper...")
print("="*60)

try:
    # Test with a simple search
    jobs = scrape_jobs(
        site_name=["mycareersfuture"],
        search_term="sustainability",
        location="Singapore",
        results_wanted=5,
        verbose=1
    )
    
    print(f"\n✅ Found {len(jobs)} jobs from MyCareersFuture")
    
    if len(jobs) > 0:
        print("\nSample jobs:")
        for i, (idx, job) in enumerate(jobs.iterrows(), 1):
            print(f"\n{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Site: {job.get('site', 'N/A')}")
            print(f"   URL: {job.get('job_url', 'N/A')}")
    else:
        print("⚠️  No jobs found - this might indicate an issue with the scraper")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("MyCareersFuture scraper test completed!")
