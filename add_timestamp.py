#!/usr/bin/env python3
"""Add timestamp comment to HTML file to ensure it always changes"""
import re
from datetime import datetime

timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
comment = f"<!-- Auto-generated timestamp: {timestamp} -->"

try:
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove old timestamp if exists
    content = re.sub(r'<!-- Auto-generated timestamp:.*?-->', '', content)
    
    # Add timestamp before </head>
    if '</head>' in content:
        content = content.replace('</head>', f'{comment}\n</head>')
    else:
        # If no </head>, add at the beginning
        content = comment + '\n' + content
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added timestamp comment to index.html: {timestamp}")
except Exception as e:
    print(f"⚠️  Could not update timestamp: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
