# Quick Start Guide

## 🚀 Deploy Your Website in 3 Steps

### Step 1: Generate the Website
```bash
python search_core_impact_jobs.py
```
This will:
- Search for jobs across Indeed, LinkedIn, and Google
- Generate `index.html` with all jobs
- Save data to `singapore_core_impact_jobs.csv`

### Step 2: Deploy to GitHub Pages (Easiest)

1. **Create a new GitHub repository** (or use existing)
2. **Upload files:**
   ```bash
   git init
   git add index.html
   git commit -m "Deploy impact jobs website"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/impact-jobs.git
   git push -u origin main
   ```
3. **Enable GitHub Pages:**
   - Go to Settings → Pages
   - Select "main" branch
   - Your site is live! 🎉

### Step 3: Share Your Website
Your website will be available at:
```
https://YOUR_USERNAME.github.io/impact-jobs/
```

## ✨ Website Features

- 🔍 **Search** - Find jobs by title, company, or location
- 🏷️ **Filter** - Filter by LinkedIn, Indeed, or Google
- 📅 **Sort** - Sort by date, company, or title
- 📱 **Responsive** - Works on all devices
- ⚡ **Fast** - Single HTML file, loads instantly

## 🔄 Keep It Updated

Run the search script daily to keep jobs fresh:
```bash
python search_core_impact_jobs.py
git add index.html
git commit -m "Update jobs"
git push
```

Or set up automatic updates (see DEPLOYMENT.md for GitHub Actions)

## 📖 More Options

See `DEPLOYMENT.md` for:
- Netlify deployment
- Vercel deployment
- Custom domain setup
- Automated updates

---

**That's it!** Your website is ready to share with job seekers. 🌱
