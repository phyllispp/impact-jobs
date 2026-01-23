# Deployment Guide - Core Impact Jobs Website

This guide will help you deploy your job search website so everyone can access it.

## Quick Deploy Options

### Option 1: GitHub Pages (Free & Easy) ⭐ Recommended

1. **Create a GitHub repository:**
   ```bash
   git init
   git add index.html
   git commit -m "Initial commit: Impact jobs website"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/impact-jobs-singapore.git
   git push -u origin main
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select **main branch**
   - Click **Save**
   - Your site will be live at: `https://YOUR_USERNAME.github.io/impact-jobs-singapore/`

3. **Update the website:**
   ```bash
   python search_core_impact_jobs.py  # Generate new jobs
   git add index.html singapore_core_impact_jobs.csv
   git commit -m "Update jobs"
   git push
   ```

### Option 2: Netlify (Free & Automatic)

1. **Sign up at [netlify.com](https://netlify.com)**

2. **Deploy:**
   - Drag and drop your `index.html` file to Netlify
   - Or connect your GitHub repository for automatic deployments

3. **Your site will be live immediately** at a URL like: `https://random-name-123.netlify.app`

4. **Auto-update:** Set up GitHub integration to automatically deploy when you push updates

### Option 3: Vercel (Free & Fast)

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Follow the prompts** - your site will be live in seconds!

### Option 4: Cloudflare Pages (Free)

1. **Sign up at [pages.cloudflare.com](https://pages.cloudflare.com)**

2. **Connect your GitHub repository** or upload files directly

3. **Deploy** - your site will be live instantly

## Features of the Deployable Website

✅ **Search functionality** - Search jobs by title, company, or location  
✅ **Filter by site** - Filter by LinkedIn, Indeed, or Google  
✅ **Sort options** - Sort by date, company, or title  
✅ **Responsive design** - Works on mobile, tablet, and desktop  
✅ **Fast loading** - Single HTML file, no external dependencies  
✅ **Professional design** - Modern gradient design with smooth animations  

## Updating the Website

### Manual Update

1. Run the search script:
   ```bash
   python search_core_impact_jobs.py
   ```

2. This will automatically regenerate `index.html` with the latest jobs

3. Commit and push to your hosting service:
   ```bash
   git add index.html singapore_core_impact_jobs.csv
   git commit -m "Update jobs - $(date +%Y-%m-%d)"
   git push
   ```

### Automated Updates (Recommended)

Set up a cron job or GitHub Actions to automatically run the search script daily:

**GitHub Actions example** (`.github/workflows/update-jobs.yml`):
```yaml
name: Update Jobs Daily

on:
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run search
        run: python search_core_impact_jobs.py
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add index.html singapore_core_impact_jobs.csv
          git diff --staged --quiet || git commit -m "Auto-update jobs - $(date +%Y-%m-%d)"
          git push
```

## Custom Domain (Optional)

### GitHub Pages
1. Add a `CNAME` file with your domain name
2. Update DNS records:
   - Type: `CNAME`
   - Name: `@` or `www`
   - Value: `YOUR_USERNAME.github.io`

### Netlify/Vercel
1. Go to Domain Settings
2. Add your custom domain
3. Follow DNS configuration instructions

## File Structure

```
.
├── index.html                          # Main website (deploy this!)
├── singapore_core_impact_jobs.csv      # Job data (optional to deploy)
├── search_core_impact_jobs.py          # Search script
├── generate_deployable_website.py      # Website generator
└── DEPLOYMENT.md                       # This file
```

## Tips

- **Keep it updated:** Set up automatic daily updates so visitors always see fresh jobs
- **Share the link:** Once deployed, share your website URL with job seekers
- **Monitor traffic:** Use Google Analytics or similar to track visitors
- **SEO:** The website includes meta tags for better search engine visibility

## Troubleshooting

**Website not updating?**
- Make sure you're pushing the new `index.html` file
- Clear your browser cache
- Check that your hosting service has deployed the latest version

**Jobs not showing?**
- Make sure `singapore_core_impact_jobs.csv` exists
- Run `python search_core_impact_jobs.py` to generate fresh data
- Check browser console for JavaScript errors

**Need help?**
- Check the hosting service's documentation
- Ensure all files are committed and pushed
- Verify the HTML file is valid (open it locally first)

## Security Notes

- The website is static HTML with no backend - very secure
- All job links open in new tabs with `rel="noopener noreferrer"`
- No user data is collected or stored
- All data comes from public job listings

Happy deploying! 🚀
