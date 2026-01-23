from __future__ import annotations

import math
import time
import random
import json
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup

from jobspy.model import (
    Scraper,
    ScraperInput,
    Site,
    JobPost,
    Location,
    JobResponse,
    Country,
    DescriptionFormat,
)
from jobspy.util import (
    extract_emails_from_text,
    markdown_converter,
    create_session,
    create_logger,
    remove_attributes,
)
from jobspy.jobstreet.constant import headers
from jobspy.jobstreet.util import parse_location, parse_date, is_job_remote

log = create_logger("Jobstreet")


class Jobstreet(Scraper):
    # Jobstreet uses different domains for different countries
    # Note: Jobstreet is protected by Cloudflare, so scraping may require JavaScript execution
    base_url_sg = "https://sg.jobstreet.com"
    base_url_hk = "https://sg.jobstreet.com"  # Use Singapore domain, filter by location
    search_url_sg = "https://sg.jobstreet.com"
    search_url_hk = "https://sg.jobstreet.com"  # Use Singapore domain
    delay = 2
    band_delay = 3
    jobs_per_page = 20

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        """
        Initializes Jobstreet scraper
        """
        super().__init__(Site.JOBSTREET, proxies=proxies, ca_cert=ca_cert)
        self.session = create_session(
            proxies=self.proxies,
            ca_cert=ca_cert,
            is_tls=False,
            has_retry=True,
            delay=5,
            clear_cookies=True,
        )
        self.session.headers.update(headers)
        self.scraper_input = None
        self.seen_urls = set()

    def _get_base_url(self, location: str = None) -> str:
        """Get the appropriate base URL based on location"""
        # Jobstreet Singapore domain works for both Singapore and Hong Kong
        return self.base_url_sg

    def _get_search_url(self, location: str = None) -> str:
        """Get the appropriate search URL based on location"""
        # Jobstreet Singapore domain works for both Singapore and Hong Kong
        return self.search_url_sg

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrapes Jobstreet for jobs with scraper_input criteria
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        page = 1
        request_count = 0

        # Determine base URL based on location
        location_str = scraper_input.location or ""
        base_url = self._get_base_url(location_str)
        search_url = self._get_search_url(location_str)

        continue_search = lambda: len(job_list) < scraper_input.results_wanted

        while continue_search():
            request_count += 1
            log.info(
                f"search page: {request_count} / {math.ceil(scraper_input.results_wanted / self.jobs_per_page)}"
            )

            try:
                # Try to use API endpoint first
                jobs, has_more = self._scrape_page_api(page, base_url, search_url)
                
                if not jobs:
                    # Fallback to HTML scraping
                    jobs, has_more = self._scrape_page_html(page, base_url, search_url)

                if not jobs:
                    log.info(f"found no jobs on page: {page}")
                    break

                for job in jobs:
                    if job.job_url not in self.seen_urls:
                        self.seen_urls.add(job.job_url)
                        job_list.append(job)
                        if not continue_search():
                            break

                if not has_more:
                    break

                page += 1
                time.sleep(random.uniform(self.delay, self.delay + self.band_delay))

            except Exception as e:
                log.error(f"Error scraping page {page}: {str(e)}")
                break

        job_list = job_list[: scraper_input.results_wanted]
        return JobResponse(jobs=job_list)

    def _scrape_page_api(self, page: int, base_url: str, search_url: str) -> tuple[list[JobPost], bool]:
        """
        Attempts to scrape using API endpoint
        Note: Jobstreet doesn't have a public API, so this will likely fail
        and fall back to HTML scraping (which also requires Cloudflare bypass)
        """
        try:
            # Jobstreet doesn't have a documented public API
            # These endpoints are guesses and likely won't work
            api_urls = [
                f"{base_url}/api/chalice-search/v4/search",
                f"{base_url}/api/job-search",
                f"{base_url}/api/v1/jobs",
            ]
            
            params = {
                "q": self.scraper_input.search_term or "",
                "page": page,
                "pageSize": self.jobs_per_page,
            }
            
            if self.scraper_input.location:
                location_str = self.scraper_input.location.lower()
                if "singapore" in location_str or "sg" in location_str:
                    params["location"] = "Singapore"
                elif "hong kong" in location_str or "hk" in location_str:
                    params["location"] = "Hong Kong"
                else:
                    params["location"] = self.scraper_input.location

            for api_url in api_urls:
                try:
                    response = self.session.get(api_url, params=params, timeout=10)
                    
                    # Check for Cloudflare
                    if response.status_code == 403 or "Just a moment" in response.text:
                        continue
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            jobs = []
                            
                            # Parse API response - Jobstreet structure (if it exists)
                            job_items = data.get("results", []) or data.get("jobs", []) or data.get("data", {}).get("jobs", [])
                            
                            for item in job_items:
                                job = self._parse_api_job(item, base_url)
                                if job:
                                    jobs.append(job)
                            
                            if jobs:
                                has_more = len(job_items) == self.jobs_per_page
                                return jobs, has_more
                        except json.JSONDecodeError:
                            continue
                except Exception:
                    continue
        except Exception as e:
            log.debug(f"API scraping failed (expected - Jobstreet has no public API): {str(e)}")
        
        return [], False

    def _scrape_page_html(self, page: int, base_url: str, search_url: str) -> tuple[list[JobPost], bool]:
        """
        Scrapes jobs from HTML page
        Note: Jobstreet is protected by Cloudflare, so HTML scraping may not work
        without JavaScript execution or Cloudflare bypass.
        """
        try:
            # Jobstreet uses URL pattern: https://sg.jobstreet.com/{search-term}-jobs
            # For example: https://sg.jobstreet.com/sustainability-jobs
            search_term = (self.scraper_input.search_term or "").strip().lower().replace(" ", "-")
            
            if not search_term:
                return [], False
            
            # Construct the search URL
            if page == 1:
                url = f"{search_url}/{search_term}-jobs"
            else:
                url = f"{search_url}/{search_term}-jobs?page={page}"
            
            # Add location filter if specified (Jobstreet uses query params for location)
            if self.scraper_input.location:
                location_str = self.scraper_input.location.lower()
                if "hong kong" in location_str or "hk" in location_str:
                    url += "&location=Hong+Kong"
                elif "singapore" in location_str or "sg" in location_str:
                    url += "&location=Singapore"

            response = self.session.get(url, timeout=10)
            
            # Check for Cloudflare challenge
            if response.status_code == 403 or "Just a moment" in response.text or "challenge-platform" in response.text:
                log.warning("Cloudflare protection detected. Jobstreet HTML scraping requires JavaScript execution or Cloudflare bypass.")
                return [], False
            
            if response.status_code != 200:
                log.debug(f"HTTP {response.status_code} response from Jobstreet")
                return [], False

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find job listings in HTML
            jobs = []
            
            # Look for embedded JSON data (Jobstreet uses React)
            script_tags = soup.find_all("script", type="application/json")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if "results" in data or "jobs" in data or "jobList" in data:
                        job_items = data.get("results", []) or data.get("jobs", []) or data.get("jobList", [])
                        for item in job_items:
                            job = self._parse_json_job(item, base_url)
                            if job:
                                jobs.append(job)
                        break
                except:
                    continue
            
            # If no JSON found, try parsing HTML directly
            if not jobs:
                # Look for job card elements - Jobstreet structure
                job_selectors = [
                    ("article", {"data-testid": lambda x: x and "job-card" in (x or "").lower()}),
                    ("div", {"class": lambda c: c and "job-card" in (c or "").lower()}),
                    ("div", {"data-automation": lambda x: x and "job" in (x or "").lower()}),
                    ("div", {"id": lambda x: x and "job" in (x or "").lower()}),
                ]
                
                for tag_name, attrs in job_selectors:
                    job_cards = soup.find_all(tag_name, attrs)
                    if job_cards:
                        for card in job_cards:
                            job = self._parse_html_job(card, base_url)
                            if job:
                                jobs.append(job)
                        if jobs:
                            break
                
                # Try more generic selectors
                if not jobs:
                    # Look for links that contain job IDs
                    job_links = soup.find_all("a", href=lambda x: x and ("/job/" in x or "/jobs/" in x))
                    for link in job_links[:self.jobs_per_page]:
                        job = self._parse_html_job_from_link(link, base_url)
                        if job:
                            jobs.append(job)
            
            has_more = len(jobs) == self.jobs_per_page
            return jobs, has_more

        except Exception as e:
            log.error(f"HTML scraping error: {str(e)}")
            return [], False

    def _parse_api_job(self, item: dict, base_url: str) -> Optional[JobPost]:
        """Parse job from API response"""
        try:
            job_id = item.get("id") or item.get("jobId") or item.get("job_id") or f"jobstreet-{hash(item.get('url', ''))}"
            title = item.get("title") or item.get("jobTitle") or item.get("job_title", "N/A")
            company = item.get("company") or item.get("companyName") or item.get("company_name", "N/A")
            location_text = item.get("location") or item.get("jobLocation") or item.get("job_location", "Singapore")
            job_url = item.get("url") or item.get("jobUrl") or item.get("job_url")
            
            if job_url and not job_url.startswith("http"):
                job_url = urljoin(base_url, job_url)
            elif not job_url:
                job_url = f"{base_url}/job/{job_id}" if job_id else f"{base_url}/jobs/{job_id}"

            # Parse date
            date_posted = None
            date_str = item.get("postedDate") or item.get("datePosted") or item.get("posted_date")
            if date_str:
                date_posted = parse_date(date_str)

            # Parse location
            location = parse_location(location_text)

            # Get description
            description = item.get("description") or item.get("jobDescription") or item.get("job_description", "")

            return JobPost(
                id=f"jobstreet-{job_id}",
                title=title,
                company_name=company,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                description=description,
                is_remote=is_job_remote(title, description, location),
                emails=extract_emails_from_text(description),
            )
        except Exception as e:
            log.error(f"Error parsing API job: {str(e)}")
            return None

    def _parse_json_job(self, item: dict, base_url: str) -> Optional[JobPost]:
        """Parse job from embedded JSON"""
        return self._parse_api_job(item, base_url)

    def _parse_html_job(self, card, base_url: str) -> Optional[JobPost]:
        """Parse job from HTML card"""
        try:
            # Find job link
            link = card.find("a", href=True)
            if not link:
                return None

            job_url = link.get("href")
            if not job_url.startswith("http"):
                job_url = urljoin(base_url, job_url)

            # Extract title
            title_elem = link.find(["h2", "h3", "span", "div"], class_=lambda c: c and "title" in (c or "").lower())
            title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True) or "N/A"
            
            # Extract company
            company_elem = card.find(["span", "div", "a"], class_=lambda c: c and "company" in (c or "").lower())
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            # Extract location
            location_elem = card.find(["span", "div"], class_=lambda c: c and ("location" in (c or "").lower() or "area" in (c or "").lower()))
            location_text = location_elem.get_text(strip=True) if location_elem else "Singapore"
            location = parse_location(location_text)

            # Extract date
            date_elem = card.find(["span", "div"], class_=lambda c: c and ("date" in (c or "").lower() or "time" in (c or "").lower()))
            date_posted = None
            if date_elem:
                date_posted = parse_date(date_elem.get_text(strip=True))

            return JobPost(
                id=f"jobstreet-{hash(job_url)}",
                title=title,
                company_name=company,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                is_remote=is_job_remote(title, location=location),
            )
        except Exception as e:
            log.error(f"Error parsing HTML job: {str(e)}")
            return None

    def _parse_html_job_from_link(self, link, base_url: str) -> Optional[JobPost]:
        """Parse job from a link element"""
        try:
            job_url = link.get("href")
            if not job_url.startswith("http"):
                job_url = urljoin(base_url, job_url)

            # Extract title from link text
            title = link.get_text(strip=True) or "N/A"
            
            # Try to find parent container for more info
            parent = link.find_parent(["div", "article", "li"])
            company = "N/A"
            location_text = "Singapore"
            
            if parent:
                company_elem = parent.find(["span", "div"], class_=lambda c: c and "company" in (c or "").lower())
                if company_elem:
                    company = company_elem.get_text(strip=True)
                
                location_elem = parent.find(["span", "div"], class_=lambda c: c and "location" in (c or "").lower())
                if location_elem:
                    location_text = location_elem.get_text(strip=True)

            location = parse_location(location_text)

            return JobPost(
                id=f"jobstreet-{hash(job_url)}",
                title=title,
                company_name=company,
                location=location,
                job_url=job_url,
                is_remote=is_job_remote(title, location=location),
            )
        except Exception as e:
            log.error(f"Error parsing job from link: {str(e)}")
            return None
