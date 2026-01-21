#!/usr/bin/env python3
"""
Quick script to generate and preview the website locally
"""
import os
import sys
import webbrowser
from pathlib import Path
from generate_deployable_website import generate_deployable_website

def main():
    # Look for CSV files
    csv_files = [
        'core_impact_jobs_sg_hk.csv',
        'singapore_core_impact_jobs.csv',
        'indeed_singapore_core_impact_jobs.csv',
    ]
    
    csv_file = None
    for file in csv_files:
        if os.path.exists(file):
            csv_file = file
            print(f"Found CSV file: {csv_file}")
            break
    
    if not csv_file:
        print("No CSV file found. Please run search_core_impact_jobs.py first.")
        print("\nAvailable CSV files:")
        for f in Path('.').glob('*.csv'):
            print(f"  - {f}")
        return
    
    # Generate website
    output_file = 'index.html'
    print(f"\nGenerating website from {csv_file}...")
    try:
        generate_deployable_website(csv_file, output_file)
        print(f"✅ Website generated: {output_file}")
        
        # Get absolute path
        abs_path = os.path.abspath(output_file)
        file_url = f"file://{abs_path}"
        
        print(f"\n📂 File location: {abs_path}")
        print(f"🌐 Opening in browser...")
        
        # Open in default browser
        webbrowser.open(file_url)
        
        print(f"\n✅ Website opened in your browser!")
        print(f"\nTo open manually:")
        print(f"  1. Open Finder and navigate to: {os.path.dirname(abs_path)}")
        print(f"  2. Double-click on '{output_file}'")
        print(f"\nOr use this command:")
        print(f"  open {abs_path}")
        
    except Exception as e:
        print(f"❌ Error generating website: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
