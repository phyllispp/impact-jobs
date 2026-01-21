# Automatic Daily Updates Setup

## How It Works

GitHub Actions will automatically:
1. Run your Python script daily at 2 AM UTC (10 AM Singapore time)
2. Crawl job sites (Indeed, LinkedIn, Google, MyCareersFuture) in Singapore and Hong Kong
3. Generate new `index.html` and `core_impact_jobs_sg_hk.csv`
4. Commit and push changes
5. GitHub Pages automatically updates your website

## Setup Steps

### Step 1: Deploy Website First ✅

```bash
# Initialize git (if not already done)
git init

# Add all necessary files
git add index.html
git add singapore_core_impact_jobs.csv
git add search_core_impact_jobs.py
git add generate_deployable_website.py
git add requirements.txt

# Commit
git commit -m "Initial deploy"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/impact-jobs.git
git push -u origin main
```

**Then enable GitHub Pages:**
- Go to Settings → Pages
- Select "main" branch
- Save

### Step 2: Add Automatic Updates

```bash
# Add the workflow file
git add .github/workflows/update-jobs-daily.yml

# Commit
git commit -m "Add automatic daily updates"

# Push
git push
```

**That's it!** The workflow will start running automatically.

## What Files Need to Be in GitHub?

Make sure these files are committed:

```
✅ index.html                          # Website (will be auto-updated)
✅ core_impact_jobs_sg_hk.csv         # Job data (will be auto-updated)
✅ search_core_impact_jobs.py         # Search script
✅ generate_deployable_website.py     # Website generator
✅ requirements.txt                    # Python dependencies
✅ jobspy/                             # Job scraping library (local)
✅ .github/workflows/update-jobs-daily.yml  # Workflow file
```

## How to Test

### Manual Trigger

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Update Jobs Daily** workflow
4. Click **Run workflow** button
5. Select branch: `main`
6. Click **Run workflow**

This will run immediately so you can test it!

### Check Results

After the workflow runs:
- Check the **Actions** tab to see if it succeeded
- Check your repository - `index.html` should be updated
- Visit your GitHub Pages site - should show new jobs

## Schedule Customization

To change when it runs, edit `.github/workflows/update-jobs-daily.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # 2 AM UTC daily
```

**Cron format:** `minute hour day month weekday`

Examples:
- `'0 2 * * *'` - Daily at 2 AM UTC
- `'0 10 * * *'` - Daily at 10 AM UTC  
- `'0 2 * * 1'` - Every Monday at 2 AM UTC
- `'0 */6 * * *'` - Every 6 hours

## Troubleshooting

### Workflow fails to install dependencies?
- Make sure `requirements.txt` is in the repository
- Check the Actions log for specific error messages

### Workflow runs but no changes?
- Jobs might not have changed
- Check the Actions log to see what happened
- The workflow only commits if there are actual changes

### Website not updating?
- Make sure GitHub Pages is enabled
- Check that `index.html` is being updated in the repository
- GitHub Pages updates automatically when files change

### Need to update more frequently?
- Change the cron schedule in the workflow file
- Or trigger manually from the Actions tab

## Important Notes

⚠️ **Rate Limiting:**
- LinkedIn may rate limit if you run too frequently
- Daily updates should be fine
- If you get blocked, reduce frequency

⚠️ **GitHub Actions Limits:**
- Free accounts: 2,000 minutes/month
- Daily runs use ~5-10 minutes each
- You have plenty of quota for daily updates

⚠️ **Repository Privacy:**
- Public repos: Unlimited Actions minutes
- Private repos: Limited free minutes
- Consider making the repo public if needed

## Monitoring

Check your workflow status:
1. Go to **Actions** tab in GitHub
2. See recent runs and their status
3. Click on a run to see detailed logs
4. Green checkmark = success ✅
5. Red X = failure ❌

---

**Your website will now update automatically every day!** 🎉
