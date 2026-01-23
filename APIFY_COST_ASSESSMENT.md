# Apify Cost Assessment for Jobstreet (Singapore) & JobsDB (Hong Kong)

## Apify Free Tier Limits

- **Monthly Credits**: $5 USD
- **Compute Units**: $0.30 per unit (on free tier)
- **Concurrent Runs**: 3 maximum
- **Data Retention**: 7 days
- **Renewal**: Credits reset monthly (not cumulative)

## Available Scrapers & Pricing

### JobStreet Singapore Options

1. **JobStreet Job Scraper 🌏** (EasyApi)
   - **Pricing**: $19.99/month + usage charges
   - **Status**: ❌ Exceeds free tier (monthly fee alone is 4x the free credit)
   - Supports sg.jobstreet.com
   - Rating: 5.0/5 (111 users)

2. **JobStreet Scraper** (Shahid Irfan)
   - **Pricing**: Pay-per-usage (exact cost not published)
   - **Status**: ⚠️ Unknown if feasible
   - Requires residential proxies
   - Rating: 5.0/5 (18 users)

3. **Seek Job Scraper** (websift/Jacob)
   - **Pricing**: $2.50 per 1,000 results
   - **Status**: ✅ Potentially feasible for light usage
   - Supports jobstreet.com.sg
   - Rating: 5.0/5 (673 users)
   - **Cost Example**: 
     - 100 jobs = ~$0.25
     - 500 jobs = ~$1.25
     - 1,000 jobs = ~$2.50

### JobsDB Hong Kong Options

1. **JobsDB Scraper** (Lexis Solutions)
   - **Pricing**: $29/month + usage charges
   - **Status**: ❌ Exceeds free tier (monthly fee alone is 6x the free credit)
   - Supports hk.jobsdb.com
   - Rating: 5.0/5

2. **JobsDB-HK Scraper** (Mandeep)
   - **Pricing**: $11/month + usage charges
   - **Status**: ❌ Exceeds free tier (monthly fee alone is 2x the free credit)
   - Currently under maintenance
   - Rating: 5.0/5

3. **JobsDB Scraper** (Shahid Irfan)
   - **Pricing**: Pay-per-usage (exact cost not published)
   - **Status**: ⚠️ Unknown if feasible
   - Rating: 5.0/5

## Cost Analysis

### Scenario 1: Using Pay-Per-Usage Scrapers (Best Case)

**JobStreet**: Seek Job Scraper @ $2.50 per 1,000 results
- 100 jobs: ~$0.25
- 500 jobs: ~$1.25
- 1,000 jobs: ~$2.50

**JobsDB**: Pay-per-usage (estimated similar to JobStreet)
- 100 jobs: ~$0.25 (estimated)
- 500 jobs: ~$1.25 (estimated)
- 1,000 jobs: ~$2.50 (estimated)

**Total Monthly Cost** (assuming ~500 jobs per site = 1,000 total):
- JobStreet: ~$1.25
- JobsDB: ~$1.25 (estimated)
- **Total: ~$2.50** ✅ **Within $5 free tier**

### Scenario 2: Using Monthly Subscription Scrapers

**JobStreet**: EasyApi @ $19.99/month
**JobsDB**: Lexis Solutions @ $29/month
- **Total: $48.99/month** ❌ **Exceeds free tier by 10x**

## Recommendations

### ✅ Feasible Approach (Within Free Tier)

1. **Use Seek Job Scraper** for JobStreet Singapore
   - Pay-per-usage: $2.50 per 1,000 results
   - No monthly subscription fee
   - Well-rated (5.0/5, 673 users)

2. **Find pay-per-usage JobsDB scraper** or use Shahid Irfan's scraper
   - Need to verify exact pricing
   - May need to test to determine actual costs

3. **Usage Limits**:
   - Keep total monthly scraping under ~1,000-1,500 jobs combined
   - This should keep costs under $5/month

### ⚠️ Considerations

1. **Compute Units**: Additional costs beyond scraper fees
   - $0.30 per compute unit on free tier
   - Need to factor in compute costs for each run

2. **Data Retention**: Only 7 days on free tier
   - Need to download/export results promptly

3. **Concurrent Runs**: Limited to 3 simultaneous runs
   - May need to run scrapers sequentially

4. **Reliability**: Pay-per-usage scrapers may have limitations
   - Some require residential proxies (additional cost)
   - May have rate limits or restrictions

## Alternative: Self-Hosted Solution

If Apify costs become prohibitive, consider:
- Using Selenium/Playwright for JavaScript-heavy sites
- Implementing Cloudflare bypass solutions
- Using proxy services specifically for these sites
- May be more cost-effective for high-volume usage

## Conclusion

**Yes, it's possible to stay within Apify's free tier IF:**
- ✅ Use pay-per-usage scrapers (no monthly fees)
- ✅ Limit total monthly scraping to ~1,000-1,500 jobs
- ✅ Use Seek Job Scraper for JobStreet ($2.50/1,000 results)
- ✅ Find a pay-per-usage JobsDB scraper (or verify Shahid Irfan's pricing)

**Estimated Monthly Cost**: $2.50 - $4.00 (well within $5 free tier)

**However**, you'll need to:
1. Test the actual costs by running a few test scrapes
2. Monitor usage to stay within limits
3. Have a backup plan if costs exceed expectations
