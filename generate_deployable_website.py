import pandas as pd
from datetime import datetime, timedelta
import json
import os

def generate_deployable_website(csv_file='core_impact_jobs_sg_hk.csv', output_file='index.html'):
    """Generate a production-ready HTML website with filtering and sorting"""
    
    # Read the CSV file
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run the search script first.")
        return
    
    df = pd.read_csv(csv_file)
    
    # Filter to only show jobs from the last 7 days
    if 'date_posted' in df.columns:
        # Calculate cutoff date (7 days ago)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Convert date_posted to datetime, handling various formats
        def parse_date(date_str):
            if pd.isna(date_str) or str(date_str) == 'N/A' or str(date_str) == 'nan':
                return None
            try:
                # Try parsing common date formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                    try:
                        return datetime.strptime(str(date_str), fmt)
                    except ValueError:
                        continue
                # If all formats fail, try pandas to_datetime
                return pd.to_datetime(date_str)
            except:
                return None
        
        df['date_posted_parsed'] = df['date_posted'].apply(parse_date)
        
        # Filter to only jobs from last 7 days
        initial_count = len(df)
        df = df[df['date_posted_parsed'].notna() & (df['date_posted_parsed'] >= cutoff_date)]
        filtered_count = len(df)
        
        if initial_count > filtered_count:
            print(f"📅 Filtered {initial_count - filtered_count} jobs older than 7 days")
        
        # Sort by date (most recent first)
        df = df.sort_values('date_posted_parsed', ascending=False)
        
        # Drop the temporary parsed date column
        df = df.drop(columns=['date_posted_parsed'])
    
    # Convert to JSON for JavaScript
    jobs_data = []
    for idx, row in df.iterrows():
        location_str = str(row.get('location', 'N/A'))
        
        # Determine location category (Hong Kong or Singapore)
        location_category = 'Other'
        location_lower = location_str.lower()
        if 'hong kong' in location_lower or 'hk' in location_lower:
            location_category = 'Hong Kong'
        elif 'singapore' in location_lower or 'sg' in location_lower:
            location_category = 'Singapore'
        
        job = {
            'title': str(row.get('title', 'N/A')),
            'company': str(row.get('company', 'N/A')),
            'date_posted': str(row.get('date_posted', 'N/A')),
            'job_url': str(row.get('job_url', '#')),
            'site': str(row.get('site', 'unknown')).lower(),
            'location': location_str,
            'location_category': location_category
        }
        jobs_data.append(job)
    
    jobs_json = json.dumps(jobs_data, indent=2)
    
    # Count by site
    site_counts = {}
    if 'site' in df.columns:
        site_counts = df['site'].value_counts().to_dict()
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Find core impact jobs in Singapore and Hong Kong - ESG, Sustainability, Climate, and Social Impact roles">
    <title>Core Impact Jobs - Singapore & Hong Kong</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #667eea;
            --secondary: #764ba2;
            --accent: #f093fb;
            --text-dark: #2d3748;
            --text-light: #718096;
            --bg-light: #f7fafc;
            --white: #ffffff;
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 8px 15px rgba(0, 0, 0, 0.2);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-dark);
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 40px 20px;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.3em;
            opacity: 0.95;
            margin-bottom: 20px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
            flex-wrap: wrap;
        }}
        
        .stat-box {{
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 20px 30px;
            border-radius: 12px;
            color: white;
            min-width: 120px;
        }}
        
        .stat-box .number {{
            font-size: 2.5em;
            font-weight: bold;
            line-height: 1;
        }}
        
        .stat-box .label {{
            font-size: 0.95em;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .controls {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: var(--shadow);
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex: 1;
            min-width: 200px;
        }}
        
        .control-group label {{
            font-weight: 600;
            color: var(--text-dark);
            font-size: 0.9em;
        }}
        
        .control-group input,
        .control-group select {{
            padding: 10px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}
        
        .control-group input:focus,
        .control-group select:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        
        .filter-tags {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-tag {{
            padding: 6px 15px;
            background: var(--bg-light);
            border: 2px solid #e2e8f0;
            border-radius: 20px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .filter-tag:hover {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        
        .filter-tag.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        
        .jobs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }}
        
        .job-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
            border: 1px solid #e2e8f0;
        }}
        
        .job-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-hover);
        }}
        
        .job-card.hidden {{
            display: none;
        }}
        
        .job-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: var(--text-dark);
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        
        .job-company {{
            font-size: 1.1em;
            color: var(--primary);
            font-weight: 500;
            margin-bottom: 8px;
        }}
        
        .job-location {{
            font-size: 0.9em;
            color: var(--text-light);
            margin-bottom: 15px;
        }}
        
        .job-meta {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: auto;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }}
        
        .job-meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            color: var(--text-light);
        }}
        
        .job-link {{
            display: inline-block;
            margin-top: 15px;
            padding: 12px 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            text-align: center;
            transition: opacity 0.3s ease;
            width: 100%;
        }}
        
        .job-link:hover {{
            opacity: 0.9;
        }}
        
        .site-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 10px;
        }}
        
        .site-linkedin {{
            background: #0077b5;
            color: white;
        }}
        
        .site-indeed {{
            background: #2164f3;
            color: white;
        }}
        
        .site-google {{
            background: #4285f4;
            color: white;
        }}
        
        .site-mcareersfuture {{
            background: #5e2ca5;
            color: white;
        }}
        
        .site-jobsdb {{
            background: #fdc221;
            color: #2d3748;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: white;
            font-size: 1.2em;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 60px;
            padding: 30px 20px;
            opacity: 0.9;
        }}
        
        .footer a {{
            color: white;
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .jobs-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stats {{
                flex-direction: column;
                align-items: center;
            }}
            
            .controls {{
                flex-direction: column;
            }}
            
            .control-group {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 Core Impact Jobs</h1>
            <p>Singapore & Hong Kong • Last 7 Days</p>
            <div class="stats">
                <div class="stat-box">
                    <div class="number" id="total-jobs">{len(df)}</div>
                    <div class="label">Total Jobs</div>
                </div>
"""
    
    # Add site breakdown
    for site, count in site_counts.items():
        site_name = site.capitalize()
        html_content += f"""
                <div class="stat-box">
                    <div class="number">{count}</div>
                    <div class="label">{site_name} Jobs</div>
                </div>
"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="search">🔍 Search Jobs</label>
                <input type="text" id="search" placeholder="Search by title, company, or location...">
            </div>
            <div class="control-group">
                <label for="sort">📅 Sort By</label>
                <select id="sort">
                    <option value="date-desc">Newest First</option>
                    <option value="date-asc">Oldest First</option>
                    <option value="company">Company A-Z</option>
                    <option value="title">Title A-Z</option>
                </select>
            </div>
            <div class="control-group">
                <label>Filter by Location</label>
                <div class="filter-tags">
                    <span class="filter-tag active" data-location="all">All Locations</span>
                    <span class="filter-tag" data-location="Singapore">Singapore</span>
                    <span class="filter-tag" data-location="Hong Kong">Hong Kong</span>
                </div>
            </div>
            <div class="control-group">
                <label>Filter by Site</label>
                <div class="filter-tags">
                    <span class="filter-tag active" data-site="all">All Sites</span>
"""
    
    for site in site_counts.keys():
        site_name = site.capitalize()
        html_content += f"""
                    <span class="filter-tag" data-site="{site}">{site_name}</span>
"""
    
    html_content += """
                </div>
            </div>
        </div>
        
        <div class="jobs-grid" id="jobs-grid">
"""
    
    # Jobs will be rendered by JavaScript
    
    html_content += """
        </div>
        
        <div class="no-results hidden" id="no-results">
            <p>No jobs found matching your criteria.</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Try adjusting your search or filters.</p>
        </div>
        
        <div class="footer">
            <p>Generated on """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</p>
            <p>Searching across Indeed, LinkedIn, and MyCareersFuture</p>
            <p style="margin-top: 5px; font-size: 0.9em;">Jobs from Singapore and Hong Kong</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Looking for impact roles? We filter for genuine ESG, Sustainability, Climate, and Social Impact positions.
            </p>
        </div>
    </div>
    
    <script>
        // Jobs data
        const jobsData = """ + jobs_json + """;
        
        let filteredJobs = [...jobsData];
        let currentSiteFilter = 'all';
        let currentLocationFilter = 'all';
        
        // Format date
        function formatDate(dateStr) {
            try {
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
            } catch {
                return dateStr;
            }
        }
        
        // Get site badge HTML
        function getSiteBadge(site) {
            const badges = {
                'linkedin': '<span class="site-badge site-linkedin">LinkedIn</span>',
                'indeed': '<span class="site-badge site-indeed">Indeed</span>',
                'google': '<span class="site-badge site-google">Google</span>',
                'mycareersfuture': '<span class="site-badge site-mcareersfuture">MyCareersFuture</span>',
                'jobsdb': '<span class="site-badge site-jobsdb">JobsDB</span>'
            };
            return badges[site] || '';
        }
        
        // Render jobs
        function renderJobs(jobs) {
            const grid = document.getElementById('jobs-grid');
            const noResults = document.getElementById('no-results');
            
            if (jobs.length === 0) {
                grid.classList.add('hidden');
                noResults.classList.remove('hidden');
                return;
            }
            
            grid.classList.remove('hidden');
            noResults.classList.add('hidden');
            
            grid.innerHTML = jobs.map(job => `
                <div class="job-card">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-company">${escapeHtml(job.company)} ${getSiteBadge(job.site)}</div>
                    ${job.location && job.location !== 'N/A' ? `<div class="job-location">📍 ${escapeHtml(job.location)}</div>` : ''}
                    <div class="job-meta">
                        <div class="job-meta-item">
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            <span>Posted: ${formatDate(job.date_posted)}</span>
                        </div>
                    </div>
                    <a href="${job.job_url}" target="_blank" rel="noopener noreferrer" class="job-link">View Job →</a>
                </div>
            `).join('');
        }
        
        // Escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Filter and sort jobs
        function filterAndSort() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const sortValue = document.getElementById('sort').value;
            
            // Filter by search term, site, and location
            let filtered = jobsData.filter(job => {
                const matchesSearch = !searchTerm || 
                    job.title.toLowerCase().includes(searchTerm) ||
                    job.company.toLowerCase().includes(searchTerm) ||
                    (job.location && job.location.toLowerCase().includes(searchTerm));
                
                const matchesSite = currentSiteFilter === 'all' || job.site === currentSiteFilter;
                
                const matchesLocation = currentLocationFilter === 'all' || 
                    (job.location_category && job.location_category === currentLocationFilter);
                
                return matchesSearch && matchesSite && matchesLocation;
            });
            
            // Sort
            filtered.sort((a, b) => {
                switch(sortValue) {
                    case 'date-desc':
                        return new Date(b.date_posted) - new Date(a.date_posted);
                    case 'date-asc':
                        return new Date(a.date_posted) - new Date(b.date_posted);
                    case 'company':
                        return a.company.localeCompare(b.company);
                    case 'title':
                        return a.title.localeCompare(b.title);
                    default:
                        return 0;
                }
            });
            
            filteredJobs = filtered;
            renderJobs(filteredJobs);
            
            // Update total count
            document.getElementById('total-jobs').textContent = filtered.length;
        }
        
        // Event listeners
        document.getElementById('search').addEventListener('input', filterAndSort);
        document.getElementById('sort').addEventListener('change', filterAndSort);
        
        // Filter tags (site and location)
        document.querySelectorAll('.filter-tag').forEach(tag => {
            tag.addEventListener('click', function() {
                // Remove active from all tags in the same group
                const parent = this.parentElement;
                parent.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Update the appropriate filter
                if (this.dataset.site !== undefined) {
                    currentSiteFilter = this.dataset.site || 'all';
                }
                if (this.dataset.location !== undefined) {
                    currentLocationFilter = this.dataset.location || 'all';
                }
                
                filterAndSort();
            });
        });
        
        // Initial render
        renderJobs(filteredJobs);
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Deployable website generated: {output_file}")
    print(f"📊 Displaying {len(df)} jobs")
    print(f"📈 Jobs by site: {dict(df['site'].value_counts())}")
    print(f"\n🚀 Ready to deploy!")
    print(f"   - Upload index.html to any web hosting service")
    print(f"   - Or use GitHub Pages, Netlify, Vercel, etc.")

if __name__ == "__main__":
    generate_deployable_website()
