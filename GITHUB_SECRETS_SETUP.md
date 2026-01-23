# Setting Up Apify API Token for GitHub Actions

## Quick Setup Guide

Since GitHub Pages only serves static files, your Python script runs via **GitHub Actions** (automated workflow). Here's how to set up the Apify API token:

## Step-by-Step Instructions

### 1. Get Your Apify API Token

1. Go to https://apify.com and sign up/login
2. Navigate to https://console.apify.com/account#/integrations
3. Copy your API token (it starts with `apify_api_...`)

### 2. Add Secret to GitHub Repository

1. **Go to your GitHub repository** (e.g., `https://github.com/yourusername/JobSpy-main`)

2. **Click on "Settings"** (top menu bar)

3. **In the left sidebar**, click **"Secrets and variables"** → **"Actions"**

4. **Click "New repository secret"** button

5. **Fill in the form**:
   - **Name**: `APIFY_API_TOKEN` (must be exactly this, case-sensitive)
   - **Secret**: Paste your Apify API token
   - **Click "Add secret"**

### 3. Verify Setup

The workflow file (`.github/workflows/update-jobs-daily.yml`) is already configured to:
- ✅ Use the `APIFY_API_TOKEN` secret
- ✅ Run daily at 2 AM UTC (10 AM Singapore time)
- ✅ Generate and commit `index.html` automatically
- ✅ Deploy to GitHub Pages

### 4. Test the Workflow

**Option A: Wait for scheduled run**
- The workflow runs automatically daily at 2 AM UTC

**Option B: Manual trigger**
1. Go to **Actions** tab in your repository
2. Click **"Update Jobs Daily"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch it run in real-time

## How It Works

```
┌─────────────────────────────────────────────┐
│  GitHub Actions (Runs Daily)                │
│  ┌───────────────────────────────────────┐  │
│  │ 1. Checkout code                      │  │
│  │ 2. Install dependencies               │  │
│  │ 3. Set APIFY_API_TOKEN (from secrets) │  │
│  │ 4. Run search_core_impact_jobs.py    │  │
│  │    - Scrapes all sites including     │  │
│  │      Apify (JobStreet SG, JobsDB HK) │  │
│  │    - Generates index.html            │  │
│  │ 5. Commit & push index.html          │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  GitHub Pages (Automatic)                   │
│  - Serves updated index.html                │
│  - Updates when file is pushed              │
└─────────────────────────────────────────────┘
```

## Important Notes

### Environment Variable vs GitHub Secrets

- **Local development**: Use `export APIFY_API_TOKEN='...'`
- **GitHub Actions**: Use repository secrets (automatically available as environment variables)
- **GitHub Pages**: Cannot run Python - only serves the generated HTML

### Security

- ✅ Secrets are encrypted and never exposed in logs
- ✅ Only repository collaborators can see/edit secrets
- ✅ Secrets are masked in workflow logs (shown as `***`)

### Cost Monitoring

- Monitor Apify usage at: https://console.apify.com/account#/usage
- Stay within $5/month free tier
- The script limits results to 30 per search to control costs

## Troubleshooting

### Workflow shows "APIFY_API_TOKEN not set"
- Verify secret name is exactly `APIFY_API_TOKEN` (case-sensitive)
- Check that secret was added in the correct repository
- Ensure workflow file references `${{ secrets.APIFY_API_TOKEN }}`

### Workflow fails with authentication error
- Verify Apify token is valid
- Check token hasn't expired
- Ensure token has necessary permissions

### No jobs from Apify in results
- Check Apify console for actor run status
- Verify you have sufficient credits
- Check workflow logs for Apify errors

## Visual Guide

```
GitHub Repository
├── Settings
│   └── Secrets and variables
│       └── Actions
│           └── New repository secret
│               ├── Name: APIFY_API_TOKEN
│               └── Secret: [your_token]
│
└── .github/workflows/update-jobs-daily.yml
    └── Uses: ${{ secrets.APIFY_API_TOKEN }}
```

## Alternative: Run Locally

If you prefer to run locally and push manually:

```bash
# Set token locally
export APIFY_API_TOKEN='your_token_here'

# Run script
python3 search_core_impact_jobs.py

# Commit and push
git add index.html core_impact_jobs_sg_hk.csv
git commit -m "Update jobs"
git push
```

GitHub Pages will automatically update when you push!
