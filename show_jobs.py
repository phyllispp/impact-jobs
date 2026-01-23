#!/usr/bin/env python3
import json
import sys
import re

# Read JSON from stdin
data = json.load(sys.stdin)
jobs = data.get('results', [])

print("="*80)
print(f"MyCareersFuture - Found {len(jobs)} sustainability jobs")
print("="*80)
print()

for i, job in enumerate(jobs, 1):
    print(f"{i}. {job.get('title', 'N/A')}")
    company = job.get('postedCompany', {}).get('name', 'N/A')
    print(f"   Company: {company}")
    
    address = job.get('address', {})
    location_parts = []
    if address.get('building'):
        location_parts.append(address['building'])
    if address.get('street'):
        location_parts.append(address['street'])
    if address.get('postalCode'):
        location_parts.append(address['postalCode'])
    location = ", ".join(location_parts) if location_parts else "Singapore"
    print(f"   Location: {location}")
    
    metadata = job.get('metadata', {})
    print(f"   Posted: {metadata.get('newPostingDate', 'N/A')}")
    print(f"   URL: {metadata.get('jobDetailsUrl', 'N/A')}")
    
    salary = job.get('salary', {})
    if salary.get('minimum') and salary.get('maximum'):
        print(f"   Salary: ${salary['minimum']:,}-${salary['maximum']:,} SGD/month")
    
    # Show description preview
    desc = job.get('description', '')
    if desc:
        # Remove HTML tags for preview
        desc_clean = re.sub(r'<[^>]+>', '', desc)
        desc_preview = desc_clean[:200].replace('\n', ' ')
        print(f"   Description: {desc_preview}...")
    
    print()
