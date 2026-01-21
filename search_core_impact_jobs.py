import csv
import sys
import os

# Ensure we can import from local jobspy directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is not installed. Please install it with: pip install pandas")
    sys.exit(1)

try:
    from jobspy import scrape_jobs
except ImportError as e:
    print(f"ERROR: Failed to import jobspy: {e}")
    print("Make sure jobspy directory exists and all dependencies are installed.")
    sys.exit(1)

try:
    from generate_deployable_website import generate_deployable_website
except ImportError as e:
    print(f"ERROR: Failed to import generate_deployable_website: {e}")
    sys.exit(1)

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

# Search queries targeting actual impact job titles AND broader impact-related terms
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

print("Searching for core impact roles across Indeed, LinkedIn, Google, MyCareersFuture, and JobsDB...")
print("Searching in Singapore and Hong Kong (MyCareersFuture: Singapore only)")
print("="*80)

# Define locations to search
locations_to_search = [
    ("Singapore", "Singapore"),
    ("Hong Kong", "Hong Kong")
]

# Search across multiple sites
sites_to_search = [
    ("indeed", {"site_name": ["indeed"]}),
    ("linkedin", {"site_name": ["linkedin"]}),
    ("google", {"site_name": ["google"]}),
    ("mycareersfuture", {"site_name": ["mycareersfuture"]}),  # Singapore only
    ("jobsdb", {"site_name": ["jobsdb"]})
]

for i, query in enumerate(search_queries, 1):
    print(f"\nSearch {i}/{len(search_queries)}: {query[:60]}...")
    
    # Search each location
    for location_name, location_value in locations_to_search:
        # Skip Hong Kong for MyCareersFuture (Singapore-only site)
        if location_name == "Hong Kong":
            sites_for_location = [s for s in sites_to_search if s[0] != "mycareersfuture"]
        else:
            sites_for_location = sites_to_search
        
        print(f"\n  Location: {location_name}")
        
        # Search each site for this location
        for site_name, site_params in sites_for_location:
            try:
                # Prepare search parameters
                search_params = {
                    "search_term": query,
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
                
                # Google needs google_search_term instead of search_term
                if site_name == "google":
                    google_query = f"{query} jobs in {location_value} since 7 days ago"
                    search_params["google_search_term"] = google_query
                    search_params.pop("search_term", None)
                    search_params.pop("hours_old", None)  # Google doesn't use hours_old
                
                print(f"    Searching {site_name}...", end=" ")
                jobs = scrape_jobs(**search_params)
                
                if len(jobs) > 0:
                    all_jobs.append(jobs)
                    print(f"Found {len(jobs)} jobs")
                else:
                    print("No jobs found")
                    
            except Exception as e:
                print(f"Error: {str(e)[:50]}")
                continue

# Combine all results
if all_jobs:
    combined_df = pd.concat(all_jobs, ignore_index=True)
    # Remove duplicates based on job_url
    combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
    
    # Filter to only jobs where the title OR description contains impact-related keywords
    def is_core_impact_role(row):
        title = str(row.get('title', '')).lower() if pd.notna(row.get('title')) else ''
        description = str(row.get('description', '')).lower() if pd.notna(row.get('description')) else ''
        company = str(row.get('company', '')).lower() if pd.notna(row.get('company')) else ''
        combined = title + ' ' + description
        
        # Exclude specific companies/roles that are false positives (check early)
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
            ('surechem', 'electrical and electronics engineering')
        ]
        for company_pattern, title_pattern in false_positive_patterns:
            if company_pattern in company and title_pattern in title:
                # Exception: if it's explicitly environmental/sustainability focused, keep it
                if not any(kw in title for kw in ['sustainability', 'environmental', 'climate', 'esg', 'green', 'clean tech']):
                    return False
        
        # Exclude common false positives by title
        false_positives_titles = [
            'maintenance', 'housekeeping', 'production', 'technician', 
            'sommelier', 'workplace coordinator', 'property officer',
            'tenancy', 'events coordinator', 'bartender', 'lobby',
            'interior designer', 'facilities engineer', 'site lead',
            'resident bartender', 'assistant manager, the grand lobby',
            'underwriter', 'underwriting',  # Insurance roles (unless specifically ESG)
            'field development engineer',  # Generic engineering
            'process engineer',  # Generic engineering (unless environmental focus)
            'project engineer',  # Generic engineering
            'shift supervisor',  # Manufacturing
            'rooms controller',
            'colo regional engineering',  # Amazon data center engineering
            'resident technical officer',  # Construction compliance, not impact
            'workplace executive'  # Administrative role
        ]
        if any(fp in title for fp in false_positives_titles):
            # Exception: if title contains ESG/sustainability/environmental explicitly, keep it
            if not any(kw in title for kw in ['esg', 'sustainability', 'environmental', 'climate', 'green']):
                return False
        
        # Skip JLL jobs (they match on "better world" but aren't impact roles)
        if 'jll' in company:
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
        # Check if description only has environmental in false positive contexts
        if 'environmental' in description.lower():
            has_real_environmental = any([
                'environmental impact' in description.lower(),
                'environmental & social' in description.lower(),
                'environmental and social' in description.lower(),
                'environmental sustainability' in description.lower(),
                'environmental risk' in description.lower(),
                'environmental due diligence' in description.lower(),
                'environmental health' in description.lower() and 'climate change' in description.lower(),
                'environmental' in title.lower()  # If in title, it's likely real
            ])
            if not has_real_environmental:
                # Check if it's just about workplace conditions
                if any(fp in description.lower() for fp in environmental_false_positives):
                    # Only exclude if title doesn't have impact keywords
                    if not any(kw in title for kw in ['sustainability', 'environmental', 'climate', 'esg', 'green']):
                        return False
        
        # Exclude insurance/underwriting roles unless they're specifically ESG/sustainability roles
        if any(term in title for term in ['underwriter', 'underwriting']):
            if not any(kw in combined for kw in ['esg', 'sustainability', 'sustainable', 'climate', 'environmental risk', 'green']):
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
            desc_has_impact = any([
                'climate change' in description.lower(),
                'sustainability' in description.lower() and ('strategy' in description.lower() or 'initiative' in description.lower()),
                'environmental impact' in description.lower(),
                'carbon' in description.lower(),
                'renewable' in description.lower(),
                'clean energy' in description.lower(),
                'green technology' in description.lower(),
                'e-sustainability' in description.lower()
            ])
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
            # If "impact" only appears in generic phrases and not in impact-related contexts, exclude
            has_generic_only = any(phrase in description.lower() for phrase in generic_impact_phrases)
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
        # Check for CSR/sustainability mentions that are just company descriptions
        if ('corporate social responsibility' in description.lower() or 'csr' in description.lower()) and 'csr' not in title.lower():
            # Check if CSR is mentioned in the context of role responsibilities vs company benefits
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
            has_csr_role_focus = any(context in description.lower() for context in csr_contexts)
            # If CSR is only mentioned as a company benefit/network/initiatives, exclude
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
            has_csr_benefit_only = any(phrase in description.lower() for phrase in csr_benefit_phrases)
            # For consultant roles, CSR/ESG mentioned as company initiatives is not enough
            if 'consultant' in title.lower() and has_csr_benefit_only and not has_csr_role_focus:
                return False
            # For other roles too
            if has_csr_benefit_only and not has_csr_role_focus:
                return False
        
        # Exclude legal/finance roles where sustainability is just mentioned as business area, not role focus
        legal_finance_titles = ['legal', 'counsel', 'lawyer', 'attorney', 'finance', 'accountant', 'auditor', 'treasurer']
        if any(term in title.lower() for term in legal_finance_titles):
            # Check if sustainability/sustainable finance is mentioned as role responsibility vs company description
            if 'sustainability' in description.lower() or 'sustainable finance' in description.lower():
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
                has_role_focus = any(indicator in description.lower() for indicator in role_focus_indicators)
                # Check if it's just mentioned as part of company operations
                company_desc_phrases = [
                    'digital banking and sustainability',
                    'sustainability, and working',
                    'sustainability and working',
                    'footprint * sustainable finance',
                    'footprint sustainable finance',
                    'extensive footprint sustainable finance'
                ]
                has_company_desc_only = any(phrase in description.lower() for phrase in company_desc_phrases)
                if has_company_desc_only and not has_role_focus:
                    return False
        
        # Exclude roles where "sustainable" only appears in generic business contexts
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
            has_sustainable_role_focus = any(indicator in description.lower() for indicator in sustainable_role_indicators)
            # Generic business language (commercial sustainability, not environmental)
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
            has_generic_only = any(phrase in description.lower() for phrase in generic_sustainable) and not has_sustainable_role_focus
            if has_generic_only:
                return False
        
        # Exclude roles where CSR/social impact is only mentioned as part of activities/initiatives for non-impact roles
        if ('corporate social responsibility' in description.lower() or 'csr' in description.lower() or 'social impact' in description.lower()) and not any(kw in title.lower() for kw in ['csr', 'social impact', 'sustainability', 'esg']):
            # Check if CSR/social impact is mentioned as role responsibility vs just activities
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
            # Check if it's just mentioned as activities/initiatives for non-impact roles
            csr_activities_only = any([
                'csr initiatives' in description.lower() and 'participate' in description.lower(),
                'csr activities' in description.lower() and 'support' in description.lower(),
                'corporate social responsibility initiatives' in description.lower() and 'participate' in description.lower(),
                'social impact' in description.lower() and 'commitment to positive social impact' in description.lower() and 'intern' in title.lower()
            ])
            if csr_activities_only and not csr_role_focus:
                return False
        
        # Exclude generic roles (legal, finance, sourcing, technical director) unless they have clear impact focus in title
        generic_role_titles = ['legal counsel', 'counsel', 'manager, finance', 'finance manager', 'strategic sourcing', 'technical director', 'sourcing manager']
        if any(term in title.lower() for term in generic_role_titles):
            # Must have impact keyword in title to be considered
            if not any(kw in title.lower() for kw in ['esg', 'sustainability', 'sustainable', 'environmental', 'climate', 'green', 'csr', 'impact']):
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
                if not any(indicator in description.lower() for indicator in strong_impact_indicators):
                    return False
        
        # Check if any impact keyword appears in title or description
        # Prioritize matches in title, but also accept description matches
        matches = []
        for kw in impact_keywords:
            kw_lower = kw.lower()
            if kw_lower in title:
                matches.append(f"title:{kw}")
            elif kw_lower in description:
                matches.append(f"desc:{kw}")
        
        # Must have at least one impact keyword match
        return len(matches) > 0
    
    # Filter by title and description
    core_impact_jobs = combined_df[combined_df.apply(is_core_impact_role, axis=1)]
    
    print("\n" + "="*80)
    print(f"Total unique jobs found: {len(combined_df)}")
    print(f"Core impact roles (title/description contains impact keywords): {len(core_impact_jobs)}")
    print("="*80)
    
    if len(core_impact_jobs) > 0:
        # Sort by date
        core_impact_jobs = core_impact_jobs.sort_values('date_posted', ascending=False)
        
        print("\nCORE IMPACT JOBS:")
        print("="*80)
        for idx, row in core_impact_jobs.iterrows():
            title = str(row.get('title', '')).lower() if pd.notna(row.get('title')) else ''
            description = str(row.get('description', '')).lower() if pd.notna(row.get('description')) else ''
            
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
            print(f"Impact keywords found: {', '.join(matched_keywords[:5])}")  # Show first 5 matches
            if pd.notna(row.get('description')):
                desc_preview = str(row['description'])[:200].replace('\n', ' ')
                print(f"Description preview: {desc_preview}...")
            print(f"URL: {row['job_url']}")
            print("-"*80)
        
        # Save results
        output_filename = "core_impact_jobs_sg_hk.csv"
        core_impact_jobs.to_csv(output_filename, 
                                quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
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
        combined_df.to_csv(output_filename, 
                          quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        
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
    # Still create empty files so GitHub Actions doesn't fail
    import os
    if not os.path.exists("core_impact_jobs_sg_hk.csv"):
        pd.DataFrame().to_csv("core_impact_jobs_sg_hk.csv", index=False)
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("<!DOCTYPE html><html><head><title>No Jobs Found</title></head><body><h1>No jobs found</h1><p>Please check back later.</p></body></html>")
