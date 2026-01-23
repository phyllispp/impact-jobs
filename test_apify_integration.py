#!/usr/bin/env python3
"""
Test script for Apify integration
Run this to verify Apify setup before running the full search script
"""
import os
from jobspy.apify_integration import ApifyJobstreetSG, ApifyJobsDBHK

def test_apify_setup():
    """Test Apify integration setup"""
    print("="*80)
    print("Apify Integration Test")
    print("="*80)
    
    # Check API token
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("\n❌ APIFY_API_TOKEN not set!")
        print("\nTo set it:")
        print("  export APIFY_API_TOKEN='your_token_here'")
        print("\nGet your token from: https://console.apify.com/account#/integrations")
        return False
    
    print(f"\n✓ APIFY_API_TOKEN is set (length: {len(api_token)})")
    
    # Test JobStreet scraper
    print("\n" + "-"*80)
    print("Testing JobStreet Singapore scraper...")
    print("-"*80)
    
    scraper_sg = ApifyJobstreetSG()
    if not scraper_sg.api_token:
        print("❌ JobStreet scraper: API token not configured")
    else:
        print("✓ JobStreet scraper initialized")
        print("  Actor: websift/seek-job-scraper")
        print("  Cost: $2.50 per 1,000 results")
        print("  Note: This will make an actual API call and consume credits")
        response = input("\n  Test with a small search? (y/n): ")
        if response.lower() == 'y':
            try:
                jobs = scraper_sg.scrape("sustainability", results_wanted=5)
                print(f"  ✓ Found {len(jobs)} jobs")
                if len(jobs) > 0:
                    print(f"  Sample: {jobs[0].title} - {jobs[0].company_name}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    # Test JobsDB scraper
    print("\n" + "-"*80)
    print("Testing JobsDB Hong Kong scraper...")
    print("-"*80)
    
    scraper_hk = ApifyJobsDBHK()
    if not scraper_hk.api_token:
        print("❌ JobsDB scraper: API token not configured")
    else:
        print("✓ JobsDB scraper initialized")
        print("  Actor: shahidirfan/jobsdb-scraper")
        print("  Cost: Pay-per-usage (estimated ~$2.50 per 1,000 results)")
        print("  Note: This will make an actual API call and consume credits")
        response = input("\n  Test with a small search? (y/n): ")
        if response.lower() == 'y':
            try:
                jobs = scraper_hk.scrape("sustainability", results_wanted=5)
                print(f"  ✓ Found {len(jobs)} jobs")
                if len(jobs) > 0:
                    print(f"  Sample: {jobs[0].title} - {jobs[0].company_name}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("Test Complete")
    print("="*80)
    print("\nNext steps:")
    print("1. Monitor your Apify usage at: https://console.apify.com/account#/usage")
    print("2. Run the full search script: python3 search_core_impact_jobs.py")
    print("3. Ensure you stay within $5/month free tier limit")
    
    return True

if __name__ == "__main__":
    test_apify_setup()
