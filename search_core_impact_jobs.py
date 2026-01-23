import csv
import pandas as pd
import os
import sys

# Print startup info for debugging
print("=" * 80)
print("Starting job search script...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print("=" * 80)

try:
    from jobspy import scrape_jobs
    print("✅ Successfully imported jobspy.scrape_jobs")
except Exception as e:
    print(f"❌ Failed to import jobspy.scrape_jobs: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from generate_deployable_website import generate_deployable_website
    print("✅ Successfully imported generate_deployable_website")
except Exception as e:
    print(f"❌ Failed to import generate_deployable_website: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Apify integration (optional - only used if API token is set)
try:
    from jobspy.apify_integration import ApifyJobstreetSG, ApifyJobsDBHK
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    ApifyJobstreetSG = None
    ApifyJobsDBHK = None

# Search for CORE impact roles by targeting specific job titles
# We'll do multiple targeted searches and combine results

impact_keywords = [
    # Core impact terms
    'impact',
    'sustainability',
    'sustainable',
    'ESG',
    'CSR',
    'corporate social responsibility',
    'social impact',
    # Climate and environmental
    'climate',
    'climate change',
    'environmental',
    'environmental health',
    'environmental & social',
    'environmental and social',
    'e-sustainability',
    # Finance
    'sustainable finance',
    'green finance',
    'responsible investment',
    'impact investing',
    'impact fund',
    # Other
    'social enterprise',
    'B Corp',
    'sustainability office',
    'sustainability team',
]

# Search queries targeting actual impact job titles AND broader
# impact-related terms
search_queries = [
    # Impact roles
    '"impact manager" OR "impact analyst" OR "impact officer" OR "impact specialist"',
    # ESG roles
    '"ESG manager" OR "ESG analyst" OR "ESG officer" OR "ESG specialist" OR "ESG consultant"',
    # Sustainability roles
    '"sustainability manager" OR "sustainability director" OR "sustainability officer" OR "sustainability specialist"',
    # CSR roles
    '"CSR manager" OR "CSR director" OR "corporate social responsibility"',
    # Climate roles
    '"climate analyst" OR "climate risk" OR "climate manager" OR "climate change"',
    # Impact investing
    '"impact investing" OR "impact fund" OR "impact investor"',
    # Social impact
    '"social impact manager" OR "social impact analyst" OR "social impact officer"',
    # Sustainable finance
    '"sustainable finance" OR "green finance" OR "responsible investment"',
    # Broader searches for roles with impact focus in descriptions
    '"climate change" OR "environmental health" OR "e-sustainability"',
    '"sustainability office" OR "sustainability team"',
    '"environmental & social" OR "environmental and social"',
]

all_jobs = []

print("Searching for core impact roles across Indeed, LinkedIn, MyCareersFuture, and Apify...")
print("Searching in Singapore and Hong Kong")
print("Apify integration: JobStreet (SG) and JobsDB (HK)")
if not os.getenv("APIFY_API_TOKEN"):
    print("⚠️  WARNING: APIFY_API_TOKEN not set. Apify scraping will be skipped.")
    print("   Set it with: export APIFY_API_TOKEN='your_token_here'")
print("=" * 80)

# Define locations to search
locations_to_search = [
    ("Singapore", "Singapore"),
    ("Hong Kong", "Hong Kong")
]

# Search across multiple sites (removed Google and JobsDB - not scrapable)
# Note: Jobstreet is skipped - protected by Cloudflare
sites_to_search = [
    ("indeed", {"site_name": ["indeed"]}),
    ("linkedin", {"site_name": ["linkedin"]}),
    ("mycareersfuture", {"site_name": ["mycareersfuture"]}),  # Singapore only
]

# Hong Kong-specific sites
sites_to_search_hk = [
    ("indeed", {"site_name": ["indeed"]}),
    ("linkedin", {"site_name": ["linkedin"]}),
    # Hong Kong only (via Apify)
    ("jobsdb_hk_apify", {"site_name": ["jobsdb_hk_apify"]}),
]

# Singapore-specific sites (including Apify)
sites_to_search_sg = [
    ("indeed", {"site_name": ["indeed"]}),
    ("linkedin", {"site_name": ["linkedin"]}),
    ("mycareersfuture", {"site_name": ["mycareersfuture"]}),  # Singapore only
    # Singapore only (via Apify)
    ("jobstreet_sg_apify", {"site_name": ["jobstreet_sg_apify"]}),
]

try:
    for i, query in enumerate(search_queries, 1):
        print(f"\nSearch {i}/{len(search_queries)}: {query[:60]}...")

        # Search each location
        for location_name, location_value in locations_to_search:
            # Use different sites for Hong Kong and Singapore (includes Apify
            # sites)
            if location_name == "Hong Kong":
                sites_for_location = sites_to_search_hk
            elif location_name == "Singapore":
                sites_for_location = sites_to_search_sg
            else:
                sites_for_location = sites_to_search

            print(f"\n  Location: {location_name}")

            # Search each site for this location
            for site_name, site_params in sites_for_location:
                try:
                    # Handle Apify sites separately
                    if site_name == "jobstreet_sg_apify":
                    if not APIFY_AVAILABLE or not ApifyJobstreetSG:
                            print(
                                f"    Skipping {site_name} (Apify integration not available)")
                            continue
                        # Use Apify for JobStreet Singapore
                        apify_scraper = ApifyJobstreetSG()
                        # Simplify query for Apify (no complex OR queries)
                        import re
                        simplified = re.sub(r'["\']', '', query)
                        search_query = query  # Initialize with original query as fallback
                        match = re.search(
                        r'["\']?(\w+(?:\s+\w+)?)["\']?\s+OR',
                        simplified,
                        re.IGNORECASE)
                        if match:
                        search_query = match.group(1)
                        else:
                        words = simplified.split()
                        for word in words:
                        if word.lower() not in [
                                    'or', 'and', 'the', 'a', 'an'] and len(word) > 2:
                                search_query = word
                                break
                        if search_query == query and words:
                            search_query = words[0]

                        print(f"    Searching {site_name} via Apify...", end=" ")
                        try:
                        apify_jobs = apify_scraper.scrape(
                            search_query, results_wanted=30)
                        if len(apify_jobs) > 0:
                            # Convert to DataFrame format matching scrape_jobs
                            # output
                            jobs_list = []
                            for job in apify_jobs:
                                jobs_list.append(
                                    {
                                        'id': job.id,
                                        'site': 'jobstreet_apify',
                                        'job_url': job.job_url,
                                        'job_url_direct': job.job_url,
                                        'title': job.title,
                                        'company': job.company_name,
                                        'location': f"{job.location.city}, {job.location.country.value.title()}" if job.location.city else str(
                                            job.location.country.value),
                                        'date_posted': job.date_posted,
                                        'job_type': None,
                                        'salary_source': None,
                                        'interval': None,
                                        'min_amount': None,
                                        'max_amount': None,
                                        'currency': None,
                                        'is_remote': job.is_remote,
                                        'job_level': None,
                                        'job_function': None,
                                        'listing_type': None,
                                        'emails': None,
                                        'description': job.description or '',
                                        'company_industry': None,
                                        'company_url': None,
                                        'company_logo': None,
                                        'company_url_direct': None,
                                        'company_addresses': None,
                                        'company_num_employees': None,
                                        'company_revenue': None,
                                        'company_description': None,
                                        'skills': None,
                                        'experience_range': None,
                                        'company_rating': None,
                                        'company_reviews_count': None,
                                        'vacancy_count': None,
                                        'work_from_home_type': None,
                                    })
                            jobs_df = pd.DataFrame(jobs_list)
                            all_jobs.append(jobs_df)
                            print(f"Found {len(apify_jobs)} jobs")
                        else:
                            print("No jobs found")
                        except Exception as e:
                        error_msg = str(e)
                        print(f"Error: {error_msg[:100]}")
                        continue

                        elif site_name == "jobsdb_hk_apify":
                        if not APIFY_AVAILABLE or not ApifyJobsDBHK:
                        print(
                            f"    Skipping {site_name} (Apify integration not available)")
                        continue
                        # Use Apify for JobsDB Hong Kong
                        apify_scraper = ApifyJobsDBHK()
                        # Simplify query for Apify
                        import re
                        simplified = re.sub(r'["\']', '', query)
                        search_query = query  # Initialize with original query as fallback
                        match = re.search(
                        r'["\']?(\w+(?:\s+\w+)?)["\']?\s+OR',
                        simplified,
                        re.IGNORECASE)
                        if match:
                        search_query = match.group(1)
                        else:
                        words = simplified.split()
                        for word in words:
                        if word.lower() not in [
                                    'or', 'and', 'the', 'a', 'an'] and len(word) > 2:
                                search_query = word
                                break
                        if search_query == query and words:
                            search_query = words[0]

                        print(f"    Searching {site_name} via Apify...", end=" ")
                        try:
                        apify_jobs = apify_scraper.scrape(
                            search_query, results_wanted=30)
                        if len(apify_jobs) > 0:
                            # Convert to DataFrame format matching scrape_jobs
                            # output
                            jobs_list = []
                            for job in apify_jobs:
                                jobs_list.append(
                                    {
                                        'id': job.id,
                                        'site': 'jobsdb_hk_apify',
                                        'job_url': job.job_url,
                                        'job_url_direct': job.job_url,
                                        'title': job.title,
                                        'company': job.company_name,
                                        'location': f"{job.location.city}, {job.location.country.value.title()}" if job.location.city else str(
                                            job.location.country.value),
                                        'date_posted': job.date_posted,
                                        'job_type': None,
                                        'salary_source': None,
                                        'interval': None,
                                        'min_amount': None,
                                        'max_amount': None,
                                        'currency': None,
                                        'is_remote': job.is_remote,
                                        'job_level': None,
                                        'job_function': None,
                                        'listing_type': None,
                                        'emails': None,
                                        'description': job.description or '',
                                        'company_industry': None,
                                        'company_url': None,
                                        'company_logo': None,
                                        'company_url_direct': None,
                                        'company_addresses': None,
                                        'company_num_employees': None,
                                        'company_revenue': None,
                                        'company_description': None,
                                        'skills': None,
                                        'experience_range': None,
                                        'company_rating': None,
                                        'company_reviews_count': None,
                                        'vacancy_count': None,
                                        'work_from_home_type': None,
                                    })
                            jobs_df = pd.DataFrame(jobs_list)
                            all_jobs.append(jobs_df)
                            print(f"Found {len(apify_jobs)} jobs")
                        else:
                            print("No jobs found")
                        except Exception as e:
                        error_msg = str(e)
                        print(f"Error: {error_msg[:100]}")
                    continue

                # Some sites don't support complex OR queries - use simpler
                # keywords
                search_query = query
                if site_name in ["mycareersfuture"]:
                    import re
                    # Extract key terms from OR query - get the main keyword
                    # Remove quotes
                    simplified = re.sub(r'["\']', '', query)
                    # Extract first significant keyword (usually the main term before OR)
                    # Pattern: "keyword1" OR "keyword2" -> keyword1
                    match = re.search(
                        r'["\']?(\w+(?:\s+\w+)?)["\']?\s+OR',
                        simplified,
                        re.IGNORECASE)
                    if match:
                        search_query = match.group(1)
                    else:
                        # If no OR pattern, take first meaningful word
                        words = simplified.split()
                        # Skip common words
                        for word in words:
                            if word.lower() not in [
                                    'or', 'and', 'the', 'a', 'an'] and len(word) > 2:
                                search_query = word
                                break
                        # Fallback: use first word
                        if search_query == query and words:
                            search_query = words[0]

                # Prepare search parameters
                search_params = {
                    "search_term": search_query,
                    "location": location_value,
                    "hours_old": 168,  # Last 7 days
                    "results_wanted": 30,
                    "verbose": 0,
                    **site_params
                }

                # Indeed needs country_indeed parameter
                if site_name == "indeed":
                    if location_name == "Singapore":
                        search_params["country_indeed"] = "Singapore"
                    elif location_name == "Hong Kong":
                        search_params["country_indeed"] = "Hong Kong"

                print(f"    Searching {site_name}...", end=" ")
                jobs = scrape_jobs(**search_params)

                if len(jobs) > 0:
                    all_jobs.append(jobs)
                    print(f"Found {len(jobs)} jobs")
                else:
                    print("No jobs found")

            except Exception as e:
                error_msg = str(e)
                print(f"Error: {error_msg[:100]}")
                # Log full error for debugging site-specific issues
                if site_name in ["mycareersfuture", "jobstreet"]:
                    import traceback
                    print(f"  Full {site_name} error: {error_msg}")
                continue

# Combine all results
if all_jobs:
    combined_df = pd.concat(all_jobs, ignore_index=True)
    # Remove duplicates based on job_url
    combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')

    # Filter to only jobs where the title OR description contains
    # impact-related keywords
    def is_core_impact_role(row):
        title = str(
            row.get(
                'title',
                '')).lower() if pd.notna(
            row.get('title')) else ''
        description = str(
            row.get(
                'description',
                '')).lower() if pd.notna(
            row.get('description')) else ''
        company = str(
            row.get(
                'company',
                '')).lower() if pd.notna(
            row.get('company')) else ''
        combined = title + ' ' + description

        # Extract job responsibilities section (before company description)
        # Many job descriptions have company info sections at the end that mention impact terms
        # but aren't part of the actual job role
        job_responsibilities = description.lower()
        company_desc_markers = [
            'about ' + company.lower(),  # Company-specific (e.g., "about axa")
            'about our company',
            'about us',
            'company overview',
            'our mission',
            'our values',
            'our purpose',
            'equal opportunity employer',
            'diversity and inclusion',
            'click here to learn more',
            'learn more about',
            'company description',
            'who we are',
            # AXA-specific markers
            'about axa',
            'about axa hong kong',
            'about axa singapore',
            'axa is an equal opportunity',
            'axa hong kong and macau is a member',
            'our purpose is to act for human progress',
            'click here to learn more about our benefits'
        ]
        for marker in company_desc_markers:
            marker_pos = job_responsibilities.find(marker)
            if marker_pos != -1:
                job_responsibilities = job_responsibilities[:marker_pos]
                break

        # Exclude AXA jobs unless they're explicitly ESG/sustainability roles
        # AXA often mentions sustainability/climate in generic company
        # descriptions but roles aren't impact-focused
        if 'axa' in company:
            # Must have impact keywords in title - description mentions aren't
            # enough for AXA
            title_has_real_impact = any(
                kw in title.lower() for kw in [
                    'esg',
                    'sustainability',
                    'sustainable',
                    'environmental',
                    'climate',
                    'green',
                    'csr',
                    'social impact',
                    'impact investing',
                    'impact fund',
                    'sustainability manager',
                    'sustainability director',
                    'sustainability officer',
                    'sustainability specialist',
                    'esg manager',
                    'esg director',
                    'esg officer',
                    'climate manager',
                    'climate director',
                    'environmental manager'])

            # Check if job responsibilities explicitly state this is a sustainability/ESG role
            # Only check in the job responsibilities section, not in company
            # description
            desc_explicitly_impact_role = any(
                [
                    'responsible for sustainability' in job_responsibilities,
                    'responsible for esg' in job_responsibilities,
                    'sustainability manager' in job_responsibilities,
                    'sustainability director' in job_responsibilities,
                    'sustainability officer' in job_responsibilities,
                    'sustainability specialist' in job_responsibilities,
                    'esg manager' in job_responsibilities,
                    'esg director' in job_responsibilities,
                    'esg officer' in job_responsibilities,
                    'this role focuses on sustainability' in job_responsibilities,
                    'this role focuses on esg' in job_responsibilities,
                    'primary responsibility.*sustainability' in job_responsibilities,
                    'primary responsibility.*esg' in job_responsibilities,
                    'sustainability strategy' in job_responsibilities,
                    'sustainability initiatives' in job_responsibilities,
                    'sustainability reporting' in job_responsibilities,
                    'esg strategy' in job_responsibilities,
                    'esg initiatives' in job_responsibilities,
                    'esg reporting' in job_responsibilities,
                    'climate change' in job_responsibilities and (
                        'strategy' in job_responsibilities or 'risk' in job_responsibilities),
                    'environmental impact' in job_responsibilities,
                    'sustainable finance' in job_responsibilities,
                    'impact investing' in job_responsibilities,
                ])

            # Also check if impact keywords appear in job responsibilities (not just company description)
            # This catches cases where keywords appear but not in the explicit
            # phrases above
            impact_keywords_in_responsibilities = any([
                kw.lower() in job_responsibilities for kw in impact_keywords
            ])

            # For AXA, require explicit impact role in title OR strong indicators in job responsibilities
            # Company description mentions are NOT sufficient
            # We require either:
            # 1. Impact keywords in title, OR
            # 2. Explicit impact role phrases in job responsibilities AND
            # impact keywords present
            if not (
                title_has_real_impact or (
                    desc_explicitly_impact_role and impact_keywords_in_responsibilities)):
                return False

        # Exclude specific companies/roles that are false positives (check
        # early)
        false_positive_patterns = [
            ('amazon', 'field development engineer'),
            ('amazon', 'colo'),
            ('axa', 'underwriter'),
            ('axa', 'underwriting'),
            ('axa', 'workplace executive'),  # Administrative role, not impact
            ('pro matrix', 'project engineer'),
            ('globalfoundries', 'process engineering'),
            ('globalfoundries', 'photolithography'),
            ('3m', 'process engineer'),
            ('3m', 'tuas plant'),
            ('tech data', 'product manager'),
            ('tech data', 'presales consultant'),
            ('wsh experts', 'resident technical officer'),
            ('surechem', 'electrical and electronics engineering'),
            ("st. joseph's institution international",
             'social media marketing'),  # Marketing role, not impact
            ('st. joseph\'s institution international', 'social media marketing'),
        ]
        for company_pattern, title_pattern in false_positive_patterns:
            if company_pattern in company and title_pattern in title:
                # Exception: if it's explicitly environmental/sustainability
                # focused, keep it
                if not any(
                    kw in title for kw in [
                        'sustainability',
                        'environmental',
                        'climate',
                        'esg',
                        'green',
                        'clean tech']):
                    return False

        # Exclude all technician jobs (including Laboratory Technician - Environmental Division)
        # These are technical/support roles, not impact strategy/management
        # roles
        if 'technician' in title.lower():
            return False

        # Exclude intern roles that aren't impact-focused
        if 'intern' in title.lower() or 'internship' in title.lower():
            # Only keep if title explicitly mentions impact keywords
            if not any(
                kw in title.lower() for kw in [
                    'esg',
                    'sustainability',
                    'sustainable',
                    'environmental',
                    'climate',
                    'green',
                    'csr',
                    'social impact',
                    'impact']):
                return False

        # Exclude Asset Management intern/summer programme roles (not
        # impact-focused)
        if 'asset management' in title.lower() and ('intern' in title.lower(
        ) or 'summer' in title.lower() or 'programme' in title.lower()):
            return False

        # Exclude common false positives by title
        false_positives_titles = [
            'maintenance', 'housekeeping', 'production',
            'sommelier', 'workplace coordinator', 'property officer',
            'tenancy', 'events coordinator', 'bartender', 'lobby',
            'interior designer', 'facilities engineer', 'site lead',
            'resident bartender', 'assistant manager, the grand lobby',
            # Insurance roles (unless specifically ESG)
            'underwriter', 'underwriting',
            'field development engineer',  # Generic engineering
            'process engineer',
            # Generic engineering (unless environmental focus)
            'project engineer',  # Generic engineering
            'shift supervisor',  # Manufacturing
            'rooms controller',
            'colo regional engineering',  # Amazon data center engineering
            'resident technical officer',  # Construction compliance, not impact
            'workplace executive',  # Administrative role
            'social media marketing',
            # Marketing roles (unless CSR/sustainability marketing)
            'recruiter',  # Recruiting roles
        ]
        if any(fp in title for fp in false_positives_titles):
            # Exception: if title contains ESG/sustainability/environmental
            # explicitly, keep it
            if not any(
                kw in title for kw in [
                    'esg',
                    'sustainability',
                    'environmental',
                    'climate',
                    'green',
                    'csr']):
                return False

        # Skip JLL jobs (they match on "better world" but aren't impact roles)
        if 'jll' in company:
            return False

        # Exclude ST. JOSEPH'S INSTITUTION INTERNATIONAL LTD jobs
        # (marketing/recruiting, not impact)
        if "st. joseph's institution international" in company.lower(
        ) or "st joseph's institution international" in company.lower():
            # Only keep if it's explicitly an impact role
            if not any(
                kw in title.lower() for kw in [
                    'sustainability',
                    'esg',
                    'csr',
                    'environmental',
                    'climate',
                    'social impact']):
                return False

        # Exclude jobs where "environmental" only appears in generic contexts
        environmental_false_positives = [
            'environmental conditions',  # Workplace conditions, not environmental impact
            'environmental health and safety',  # HSE compliance, not impact role
            'environmental compliance',  # Regulatory compliance
            'environmental regulations',
            'environmental standards',
            'environmental permits'
        ]
        # Check if description only has environmental in false positive
        # contexts
        if 'environmental' in description.lower():
            has_real_environmental = any([
                'environmental impact' in description.lower(),
                'environmental & social' in description.lower(),
                'environmental and social' in description.lower(),
                'environmental sustainability' in description.lower(),
                'environmental risk' in description.lower(),
                'environmental due diligence' in description.lower(),
                'environmental health' in description.lower(
                ) and 'climate change' in description.lower(),
                'environmental' in title.lower()  # If in title, it's likely real
            ])
            if not has_real_environmental:
                # Check if it's just about workplace conditions
                if any(fp in description.lower()
                       for fp in environmental_false_positives):
                    # Only exclude if title doesn't have impact keywords
                    if not any(
                        kw in title for kw in [
                            'sustainability',
                            'environmental',
                            'climate',
                            'esg',
                            'green']):
                        return False

        # Exclude insurance/underwriting roles unless they're specifically
        # ESG/sustainability roles
        if any(term in title for term in ['underwriter', 'underwriting']):
            if not any(
                kw in combined for kw in [
                    'esg',
                    'sustainability',
                    'sustainable',
                    'climate',
                    'environmental risk',
                    'green']):
                return False

        # Exclude generic engineering roles unless they have clear impact focus
        engineering_keywords = ['engineer', 'engineering']
        if any(eng in title for eng in engineering_keywords):
            # Keep if title explicitly mentions impact keywords
            title_has_impact = any(kw in title for kw in [
                'sustainability', 'sustainable', 'environmental', 'climate',
                'esg', 'green', 'clean tech', 'renewable'
            ])
            # Keep if description has strong impact focus (not just compliance)
            desc_has_impact = any(
                [
                    'climate change' in description.lower(),
                    'sustainability' in description.lower() and (
                        'strategy' in description.lower() or 'initiative' in description.lower()),
                    'environmental impact' in description.lower(),
                    'carbon' in description.lower(),
                    'renewable' in description.lower(),
                    'clean energy' in description.lower(),
                    'green technology' in description.lower(),
                    'e-sustainability' in description.lower()])
            if not (title_has_impact or desc_has_impact):
                return False

        # Exclude generic uses of "impact" that don't indicate impact roles
        if 'impact' in description.lower() and 'impact' not in title.lower():
            # Check if it's just generic business language
            generic_impact_phrases = [
                'high-impact role',
                'high impact role',
                'make an impact',
                'make a positive impact',
                'create a global impact',
                'create global impact',
                'long-term impact',
                'long term impact',
                'significant impact',
                'maximum impact',
                'real impact',
                'meaningful impact',
                'positive impact',
                'impact and contribution',
                'impact sourcing',
                'impact role',
                'impact position',
                'potential impact',
                'their impact',
                'business impact',
                'commercial impact'
            ]
            # If "impact" only appears in generic phrases and not in
            # impact-related contexts, exclude
            has_generic_only = any(phrase in description.lower()
                                   for phrase in generic_impact_phrases)
            has_real_impact_context = any([
                'social impact' in description.lower(),
                'environmental impact' in description.lower(),
                'impact investing' in description.lower(),
                'impact fund' in description.lower(),
                'impact measurement' in description.lower(),
                'impact assessment' in description.lower(),
                'impact management' in description.lower(),
                'impact strategy' in description.lower(),
                'impact analyst' in description.lower(),
                'impact manager' in description.lower(),
                'impact officer' in description.lower(),
                'impact initiatives' in description.lower(),
                'impact programs' in description.lower()
            ])
            if has_generic_only and not has_real_impact_context:
                return False

        # Exclude roles where CSR/sustainability is only mentioned as company benefit/peripheral
        # Check for CSR/sustainability mentions that are just company
        # descriptions
        if ('corporate social responsibility' in description.lower()
                or 'csr' in description.lower()) and 'csr' not in title.lower():
            # Check if CSR is mentioned in the context of role responsibilities
            # vs company benefits
            csr_contexts = [
                'csr manager',
                'csr director',
                'csr officer',
                'csr specialist',
                'csr strategy',
                'csr initiatives',
                'csr programs',
                'csr reporting',
                'csr responsibilities',
                'csr role',
                'csr team',
                'csr function',
                'responsible for csr',
                'csr and',
                'csr,',
                'csr.'
            ]
            has_csr_role_focus = any(context in description.lower()
                                     for context in csr_contexts)
            # If CSR is only mentioned as a company
            # benefit/network/initiatives, exclude
            csr_benefit_phrases = [
                'corporate social responsibility and more',
                'csr and more',
                'including csr',
                'csr network',
                'csr groups',
                'csr activities',
                'csr committee',
                'drive initiatives in environmental social governance (esg)',
                'drive initiatives in esg',
                'esg, equality diversity',
                'esg, equality diversity & inclusion'
            ]
            has_csr_benefit_only = any(
                phrase in description.lower() for phrase in csr_benefit_phrases)
            # For consultant roles, CSR/ESG mentioned as company initiatives is
            # not enough
            if 'consultant' in title.lower() and has_csr_benefit_only and not has_csr_role_focus:
                return False
            # For other roles too
            if has_csr_benefit_only and not has_csr_role_focus:
                return False

        # Exclude legal/finance roles where sustainability is just mentioned as
        # business area, not role focus
        legal_finance_titles = [
            'legal',
            'counsel',
            'lawyer',
            'attorney',
            'finance',
            'accountant',
            'auditor',
            'treasurer']
        if any(term in title.lower() for term in legal_finance_titles):
            # Check if sustainability/sustainable finance is mentioned as role
            # responsibility vs company description
            if 'sustainability' in description.lower(
            ) or 'sustainable finance' in description.lower():
                # Look for indicators that it's actually part of the role
                role_focus_indicators = [
                    'sustainability team',
                    'sustainability office',
                    'sustainability strategy',
                    'sustainability initiatives',
                    'sustainability reporting',
                    'sustainability risk',
                    'sustainability compliance',
                    'sustainable finance team',
                    'sustainable finance products',
                    'sustainable finance business',
                    'sustainable finance strategy',
                    'sustainable finance initiatives',
                    'responsible for sustainability',
                    'support sustainability',
                    'drive sustainability',
                    'sustainability and',
                    'sustainability,',
                    'sustainability.'
                ]
                has_role_focus = any(indicator in description.lower()
                                     for indicator in role_focus_indicators)
                # Check if it's just mentioned as part of company operations
                company_desc_phrases = [
                    'digital banking and sustainability',
                    'sustainability, and working',
                    'sustainability and working',
                    'footprint * sustainable finance',
                    'footprint sustainable finance',
                    'extensive footprint sustainable finance'
                ]
                has_company_desc_only = any(
                    phrase in description.lower() for phrase in company_desc_phrases)
                if has_company_desc_only and not has_role_focus:
                    return False

        # Exclude roles where "sustainable" only appears in generic business
        # contexts
        if 'sustainable' in description.lower() and 'sustainable' not in title.lower():
            # Check if it's about sustainable business practices vs impact role
            sustainable_role_indicators = [
                'sustainability',
                'sustainable finance',
                'sustainable investment',
                'sustainable development',
                'sustainable energy',
                'sustainable technology',
                'sustainable solutions',
                'sustainable practices',
                'sustainable strategy',
                'sustainable initiatives'
            ]
            has_sustainable_role_focus = any(
                indicator in description.lower() for indicator in sustainable_role_indicators)
            # Generic business language (commercial sustainability, not
            # environmental)
            generic_sustainable = [
                'sustainable growth',
                'sustainable business',
                'sustainable operations',
                'sustainable performance',
                'sustainable competitive',
                'sustainable advantage',
                'commercial sustainability',
                'long-term commercial sustainability',
                'long term commercial sustainability',
                'financial sustainability',
                'economic sustainability'
            ]
            has_generic_only = any(phrase in description.lower(
            ) for phrase in generic_sustainable) and not has_sustainable_role_focus
            if has_generic_only:
                return False

        # Exclude roles where CSR/social impact is only mentioned as part of
        # activities/initiatives for non-impact roles
        if ('corporate social responsibility' in description.lower() or 'csr' in description.lower() or 'social impact' in description.lower(
        )) and not any(kw in title.lower() for kw in ['csr', 'social impact', 'sustainability', 'esg']):
            # Check if CSR/social impact is mentioned as role responsibility vs
            # just activities
            csr_role_focus = any([
                'csr manager' in description.lower(),
                'csr director' in description.lower(),
                'csr officer' in description.lower(),
                'csr specialist' in description.lower(),
                'csr team' in description.lower(),
                'csr function' in description.lower(),
                'responsible for csr' in description.lower(),
                'lead csr' in description.lower(),
                'drive csr' in description.lower(),
                'social impact manager' in description.lower(),
                'social impact analyst' in description.lower(),
                'social impact officer' in description.lower(),
                'social impact team' in description.lower()
            ])
            # Check if it's just mentioned as activities/initiatives for
            # non-impact roles
            csr_activities_only = any([
                'csr initiatives' in description.lower() and 'participate' in description.lower(),
                'csr activities' in description.lower() and 'support' in description.lower(),
                'corporate social responsibility initiatives' in description.lower() and 'participate' in description.lower(),
                'social impact' in description.lower() and 'commitment to positive social impact' in description.lower() and 'intern' in title.lower()
            ])
            if csr_activities_only and not csr_role_focus:
                return False

        # Exclude generic roles (legal, finance, sourcing, technical director)
        # unless they have clear impact focus in title
        generic_role_titles = [
            'legal counsel',
            'counsel',
            'manager, finance',
            'finance manager',
            'strategic sourcing',
            'technical director',
            'sourcing manager']
        if any(term in title.lower() for term in generic_role_titles):
            # Must have impact keyword in title to be considered
            if not any(
                kw in title.lower() for kw in [
                    'esg',
                    'sustainability',
                    'sustainable',
                    'environmental',
                    'climate',
                    'green',
                    'csr',
                    'impact']):
                # Check if description has strong impact focus indicators
                strong_impact_indicators = [
                    'sustainability team',
                    'sustainability office',
                    'esg team',
                    'esg office',
                    'climate change',
                    'environmental impact',
                    'social impact',
                    'impact investing',
                    'sustainable finance team',
                    'sustainable finance strategy'
                ]
                if not any(indicator in description.lower()
                           for indicator in strong_impact_indicators):
                    return False

        # Check if any impact keyword appears in title or job responsibilities
        # Prioritize matches in title, but also accept matches in job responsibilities
        # Exclude matches that only appear in company description sections
        matches = []
        title_matches = []
        desc_matches = []

        for kw in impact_keywords:
            kw_lower = kw.lower()
            if kw_lower in title:
                matches.append(f"title:{kw}")
                title_matches.append(kw_lower)
            elif kw_lower in job_responsibilities:
                matches.append(f"desc:{kw}")
                desc_matches.append(kw_lower)

        # Must have at least one impact keyword match in title OR job responsibilities
        # If only description matches exist, ensure they're in the job
        # responsibilities section
        if len(title_matches) > 0:
            return True
        elif len(desc_matches) > 0:
            # Description matches are acceptable if they're in job
            # responsibilities
            return True
        else:
            # No matches in title or job responsibilities
            return False

    # Filter by title and description
    core_impact_jobs = combined_df[combined_df.apply(
        is_core_impact_role, axis=1)]

    print("\n" + "=" * 80)
    print(f"Total unique jobs found: {len(combined_df)}")
    print(
        f"Core impact roles (title/description contains impact keywords): {len(core_impact_jobs)}")
    print("=" * 80)

    if len(core_impact_jobs) > 0:
        # Sort by date
        core_impact_jobs = core_impact_jobs.sort_values(
            'date_posted', ascending=False)

        print("\nCORE IMPACT JOBS:")
        print("=" * 80)
        for idx, row in core_impact_jobs.iterrows():
            title = str(
                row.get(
                    'title',
                    '')).lower() if pd.notna(
                row.get('title')) else ''
            description = str(
                row.get(
                    'description',
                    '')).lower() if pd.notna(
                row.get('description')) else ''

            # Find which keywords matched
            matched_keywords = []
            for kw in impact_keywords:
                kw_lower = kw.lower()
                if kw_lower in title:
                    matched_keywords.append(f"{kw} (title)")
                elif kw_lower in description:
                    matched_keywords.append(f"{kw} (description)")

            print(f"\n{row['title']}")
            print(f"Company: {row['company']}")
            print(f"Location: {row['location']}")
            print(f"Posted: {row['date_posted']}")
            # Show first 5 matches
            print(f"Impact keywords found: {', '.join(matched_keywords[:5])}")
            if pd.notna(row.get('description')):
                desc_preview = str(row['description'])[:200].replace('\n', ' ')
                print(f"Description preview: {desc_preview}...")
            print(f"URL: {row['job_url']}")
            print("-" * 80)

        # Save results
        output_filename = "core_impact_jobs_sg_hk.csv"
        core_impact_jobs.to_csv(
            output_filename,
            quoting=csv.QUOTE_NONNUMERIC,
            escapechar="\\",
            index=False)
        print(f"\n\nResults saved to '{output_filename}'")

        # Show breakdown by site
        if 'site' in core_impact_jobs.columns:
            print("\nJobs by site:")
            print(core_impact_jobs['site'].value_counts())

        # Generate HTML website
        print("\n\nGenerating deployable website...")
        try:
            generate_deployable_website(output_filename, 'index.html')
            print("✅ Website generated: index.html")
            print("   Open index.html in your browser to view the jobs!")
            print("   Ready to deploy to GitHub Pages, Netlify, Vercel, etc.")
        except Exception as e:
            print(f"⚠️  Could not generate HTML: {e}")
    else:
        print("\nNo core impact roles found with keywords in job title.")
        print("\nShowing all jobs found (may include some false positives):")
        combined_df = combined_df.sort_values('date_posted', ascending=False)
        for idx, row in combined_df.head(20).iterrows():
            print(f"\n{row['title']}")
            print(f"Company: {row['company']}")
            print(f"URL: {row['job_url']}")

        output_filename = "core_impact_jobs_sg_hk.csv"
        combined_df.to_csv(
            output_filename,
            quoting=csv.QUOTE_NONNUMERIC,
            escapechar="\\",
            index=False)

        # Generate HTML website
        print("\n\nGenerating deployable website...")
        try:
            generate_deployable_website(output_filename, 'index.html')
            print("✅ Website generated: index.html")
            print("   Ready to deploy to GitHub Pages, Netlify, Vercel, etc.")
        except Exception as e:
            print(f"⚠️  Could not generate HTML: {e}")
else:
    print("\nNo jobs found with any of the search queries.")
except Exception as e:
    import traceback
    print(f"\n❌ Fatal error occurred: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
