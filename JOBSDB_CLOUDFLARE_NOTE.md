# JobsDB/Jora Scraper - Cloudflare Protection Note

## Issue
`sg.jora.com` (JobsDB Singapore) is protected by Cloudflare, which blocks simple HTTP requests that don't execute JavaScript.

## Current Status
- The scraper is configured to use `sg.jora.com`
- API endpoint attempts may work if endpoints are discovered
- HTML scraping will fail due to Cloudflare challenge pages

## Solutions

### Option 1: Use API Endpoints (Recommended)
If you can discover the actual API endpoints used by Jora/JobsDB, update the `_scrape_page_api` method with the correct endpoints.

### Option 2: Use Cloudflare Bypass
- Use tools like `cloudscraper` Python library
- Or use a headless browser (Selenium/Playwright) to execute JavaScript

### Option 3: Alternative Source
Consider using MyCareersFuture which has a working public API, or focus on other job sites that don't have Cloudflare protection.

## Testing
To test if Cloudflare is blocking:
```bash
curl -I "https://sg.jora.com/j?q=sustainability&l=Singapore"
# Returns: HTTP/2 403 (Cloudflare challenge)
```
