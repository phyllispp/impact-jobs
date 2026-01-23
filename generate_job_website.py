import pandas as pd
from datetime import datetime
import os

def generate_html_from_csv(csv_file='singapore_core_impact_jobs.csv', output_file='index.html'):
    """Generate an HTML file displaying jobs from CSV"""
    
    # Read the CSV file
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please run the search script first.")
        return
    
    df = pd.read_csv(csv_file)
    
    # Sort by date (most recent first)
    if 'date_posted' in df.columns:
        df = df.sort_values('date_posted', ascending=False)
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Core Impact Jobs - Singapore</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 30px 20px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .stat-box {{
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
        }}
        
        .stat-box .number {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .stat-box .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .jobs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .job-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
        }}
        
        .job-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .job-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        
        .job-company {{
            font-size: 1.1em;
            color: #667eea;
            font-weight: 500;
            margin-bottom: 15px;
        }}
        
        .job-meta {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: auto;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }}
        
        .job-meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            color: #718096;
        }}
        
        .job-meta-item .icon {{
            width: 16px;
            height: 16px;
            opacity: 0.7;
        }}
        
        .job-link {{
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            text-align: center;
            transition: opacity 0.3s ease;
        }}
        
        .job-link:hover {{
            opacity: 0.9;
        }}
        
        .site-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 8px;
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
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.8;
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 Core Impact Jobs</h1>
            <p>Singapore • Last 7 Days</p>
            <div class="stats">
                <div class="stat-box">
                    <div class="number">{len(df)}</div>
                    <div class="label">Total Jobs</div>
                </div>
"""
    
    # Add site breakdown if available
    if 'site' in df.columns:
        site_counts = df['site'].value_counts()
        for site, count in site_counts.items():
            site_name = site.capitalize()
            html_content += f"""
                <div class="stat-box">
                    <div class="number">{count}</div>
                    <div class="label">{site_name} Jobs</div>
                </div>
"""
    
    html_content += """
            </div>
        </div>
        
        <div class="jobs-grid">
"""
    
    # Generate job cards
    for idx, row in df.iterrows():
        title = str(row.get('title', 'N/A')).replace('"', '&quot;')
        company = str(row.get('company', 'N/A')).replace('"', '&quot;')
        date_posted = str(row.get('date_posted', 'N/A'))
        job_url = str(row.get('job_url', '#'))
        site = str(row.get('site', 'unknown')).lower()
        
        # Format date
        try:
            date_obj = pd.to_datetime(date_posted)
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = date_posted
        
        # Site badge
        site_badge = ''
        if site == 'linkedin':
            site_badge = '<span class="site-badge site-linkedin">LinkedIn</span>'
        elif site == 'indeed':
            site_badge = '<span class="site-badge site-indeed">Indeed</span>'
        elif site == 'google':
            site_badge = '<span class="site-badge site-google">Google</span>'
        
        html_content += f"""
            <div class="job-card">
                <div class="job-title">{title}</div>
                <div class="job-company">{company} {site_badge}</div>
                <div class="job-meta">
                    <div class="job-meta-item">
                        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        <span>Posted: {formatted_date}</span>
                    </div>
                </div>
                <a href="{job_url}" target="_blank" class="job-link">View Job →</a>
            </div>
"""
    
    html_content += """
        </div>
        
        <div class="footer">
            <p>Generated on """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</p>
            <p>Searching across Indeed, LinkedIn, and Google</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML file generated: {output_file}")
    print(f"📊 Displaying {len(df)} jobs")
    if 'site' in df.columns:
        print(f"📈 Jobs by site: {dict(df['site'].value_counts())}")

if __name__ == "__main__":
    generate_html_from_csv()
