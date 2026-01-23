#!/usr/bin/env python3
"""
Simple test to check if scrapers can be imported and initialized
"""
import sys

print("Testing scraper imports...")
try:
    from jobspy.mcareersfuture import MyCareersFuture
    print("✓ MyCareersFuture imported successfully")
except Exception as e:
    print(f"✗ MyCareersFuture import failed: {e}")

try:
    from jobspy.jobsdb import JobsDB
    print("✓ JobsDB imported successfully")
except Exception as e:
    print(f"✗ JobsDB import failed: {e}")

print("\nTesting scraper initialization...")
try:
    mcf = MyCareersFuture()
    print("✓ MyCareersFuture initialized")
except Exception as e:
    print(f"✗ MyCareersFuture initialization failed: {e}")

try:
    jobsdb = JobsDB()
    print("✓ JobsDB initialized")
except Exception as e:
    print(f"✗ JobsDB initialization failed: {e}")

print("\nAll basic tests completed!")
