# GitHub Pages Deployment with Apify Integration

## How GitHub Pages Works

**Important**: GitHub Pages only serves **static HTML files**. It cannot run Python scripts.

**Workflow**:
1. GitHub Actions runs your Python script (on a schedule or manually)
2. The script generates `index.html` and `core_impact_jobs_sg_hk.csv`
3. GitHub Actions commits and pushes these files
4. GitHub Pages automatically serves the updated `index.html`

## Setting Up Apify API Token for GitHub Actions

### Step 1: Get Your Apify API Token

1. Sign up/login at https://apify.com
2. Go to https://console.apify.com/account#/integrations
3. Copy your API token (starts with `apify_api_...`)

### Step 2: Add Secret to GitHub Repository

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `APIFY_API_TOKEN`
5. Value: Paste your Apify API token
6. Click **Add secret**

### Step 3: Verify Workflow Configuration

The workflow file (`.github/workflows/update-jobs-daily.yml`) is already configured to:
- ✅ Use the `APIFY_API_TOKEN` secret
- ✅ Run the search script daily at 2 AM UTC (10 AM Singapore time)
- ✅ Commit and push the generated `index.html` file
- ✅ Deploy to GitHub Pages automatically

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (Runs Daily at 2 AM UTC)               │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 1. Checkout code                                  │ │
│  │ 2. Install Python dependencies                    │ │
│  │ 3. Set APIFY_API_TOKEN from secrets              │ │
│  │ 4. Run search_core_impact_jobs.py                │ │
│  │    - Scrapes Indeed, LinkedIn, MyCareersFuture  │ │
│  │    - Scrapes JobStreet (SG) via Apify           │ │
│  │    - Scrapes JobsDB (HK) via Apify              │ │
│  │    - Generates index.html                        │ │
│  │ 5. Commit and push index.html                    │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  GitHub Pages (Automatic)                               │
│  - Serves index.html                                    │
│  - Updates automatically when file is pushed           │
└─────────────────────────────────────────────────────────┘
```

## Manual Testing

You can manually trigger the workflow:

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Update Jobs Daily** workflow
4. Click **Run workflow** → **Run workflow**

## Monitoring

### Check Workflow Runs
- Go to **Actions** tab in your repository
- View run history and logs

### Check Apify Usage
- Monitor at https://console.apify.com/account#/usage
- Ensure you stay within $5/month free tier

### Check GitHub Pages
- Your site will be at: `https://[username].github.io/[repository-name]`
- Or custom domain if configured

## Troubleshooting

### "APIFY_API_TOKEN not set" in logs
- Verify the secret is added correctly in repository settings
- Check that the secret name is exactly `APIFY_API_TOKEN` (case-sensitive)

### Workflow fails
- Check the Actions tab for error logs
- Verify Python dependencies are in `requirements.txt`
- Ensure the script has proper error handling

### No jobs from Apify
- Check Apify console for actor run status
- Verify you have sufficient credits
- Check actor IDs are correct

## Cost Management

To stay within the free tier:
- The script limits results to 30 per search
- Monitor usage at https://console.apify.com/account#/usage
- Adjust `results_wanted` in the script if needed

## Alternative: Run Locally

If you prefer to run locally and push manually:

1. Set environment variable locally:
   ```bash
   export APIFY_API_TOKEN='your_token_here'
   ```

2. Run the script:
   ```bash
   python3 search_core_impact_jobs.py
   ```

3. Commit and push:
   ```bash
   git add index.html core_impact_jobs_sg_hk.csv
   git commit -m "Update jobs"
   git push
   ```

GitHub Pages will automatically update when you push the new `index.html`.
