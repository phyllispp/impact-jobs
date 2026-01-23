# Apify Integration Setup Guide

This guide explains how to set up Apify integration for scraping JobStreet (Singapore) and JobsDB (Hong Kong) jobs while staying within the free tier.

## Prerequisites

1. **Apify Account**: Sign up at https://apify.com (free tier available)
2. **API Token**: Get your API token from https://console.apify.com/account#/integrations

## Free Tier Limits

- **Monthly Credits**: $5 USD (resets monthly)
- **Compute Units**: $0.30 per unit
- **Concurrent Runs**: 3 maximum
- **Data Retention**: 7 days

## Cost Estimate

**JobStreet Singapore** (Seek Job Scraper by websift):
- Pricing: $2.50 per 1,000 results
- No monthly subscription fee
- Pay-per-usage only

**JobsDB Hong Kong** (JobsDB Scraper by shahidirfan):
- Pricing: Pay-per-usage (exact cost TBD, estimated similar to JobStreet)
- No monthly subscription fee

**Estimated Monthly Cost** (assuming ~500 jobs per site = 1,000 total):
- JobStreet: ~$1.25
- JobsDB: ~$1.25 (estimated)
- **Total: ~$2.50/month** ✅ **Well within $5 free tier**

## Setup Instructions

### 1. Get Your Apify API Token

1. Go to https://console.apify.com/account#/integrations
2. Copy your API token (starts with `apify_api_...`)

### 2. Set Environment Variable

**Linux/Mac:**
```bash
export APIFY_API_TOKEN='your_token_here'
```

**Windows (PowerShell):**
```powershell
$env:APIFY_API_TOKEN='your_token_here'
```

**Windows (CMD):**
```cmd
set APIFY_API_TOKEN=your_token_here
```

**Permanent Setup (Linux/Mac):**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export APIFY_API_TOKEN='your_token_here'
```

### 3. Verify Setup

Run the search script:
```bash
python3 search_core_impact_jobs.py
```

You should see:
- "Searching jobstreet_sg_apify via Apify..." messages
- "Searching jobsdb_hk_apify via Apify..." messages
- Job results from Apify if the token is valid

## Usage

The Apify integration is automatically used when:
- `APIFY_API_TOKEN` environment variable is set
- Searching for jobs in Singapore (JobStreet via Apify)
- Searching for jobs in Hong Kong (JobsDB via Apify)

The script will:
1. Simplify complex OR queries for Apify compatibility
2. Limit results to 30 per search to stay within free tier
3. Handle errors gracefully if Apify is unavailable

## Monitoring Costs

To monitor your Apify usage:
1. Go to https://console.apify.com/account#/usage
2. Check your monthly credit usage
3. Ensure you stay under $5/month

## Troubleshooting

**"Apify API token not configured"**
- Make sure `APIFY_API_TOKEN` is set as an environment variable
- Verify the token is correct at https://console.apify.com/account#/integrations

**"Actor run failed"**
- Check if you have sufficient credits
- Verify the actor IDs are correct
- Check Apify console for error details

**"No jobs found"**
- The search query might not match any jobs
- Try a simpler search term
- Check if the actor is working on Apify's platform

## Cost Optimization Tips

1. **Limit Results**: The script limits to 30 results per search to stay within free tier
2. **Combine Searches**: Use multiple search queries efficiently
3. **Monitor Usage**: Check Apify dashboard regularly
4. **Cache Results**: Download and save results to avoid re-scraping

## Alternative: Without Apify

If you prefer not to use Apify:
- The script will automatically skip Apify sites
- You'll still get results from Indeed, LinkedIn, and MyCareersFuture
- JobStreet and JobsDB will show 0 results (they're Cloudflare protected)
