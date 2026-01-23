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
from jobspy.jobsdb.constant import headers
from jobspy.jobsdb.util import parse_location, parse_date, is_job_remote

log = create_logger("JobsDB")


class JobsDB(Scraper):
    base_url = "https://sg.jora.com"
    search_url = "https://sg.jora.com/j"
    delay = 2
    band_delay = 3
    jobs_per_page = 20

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        """
        Initializes JobsDB scraper
        """
        super().__init__(Site.JOBSDB, proxies=proxies, ca_cert=ca_cert)
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

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrapes JobsDB for jobs with scraper_input criteria
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        page = 1
        request_count = 0

        continue_search = lambda: len(job_list) < scraper_input.results_wanted

        while continue_search():
            request_count += 1
            log.info(
                f"search page: {request_count} / {math.ceil(scraper_input.results_wanted / self.jobs_per_page)}"
            )

            try:
                # Try to use API endpoint first
                jobs, has_more = self._scrape_page_api(page)
                
                if not jobs:
                    # Fallback to HTML scraping
                    jobs, has_more = self._scrape_page_html(page)

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

    def _scrape_page_api(self, page: int) -> tuple[list[JobPost], bool]:
        """
        Attempts to scrape using API endpoint
        """
        try:
            # Try Jora/Seek API endpoints (Jora is part of Seek network)
            api_urls = [
                "https://sg.jora.com/api/chalice-search/v4/search",
                "https://www.seek.com.sg/api/chalice-search/v4/search",
            ]
            
            params = {
                "q": self.scraper_input.search_term or "",
                "page": page,
                "pageSize": self.jobs_per_page,
            }
            
            if self.scraper_input.location:
                params["l"] = self.scraper_input.location

            for api_url in api_urls:
                try:
                    response = self.session.get(api_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            jobs = []
                            
                            # Parse API response - Seek/Jora structure
                            job_items = data.get("results", []) or data.get("jobs", []) or data.get("data", {}).get("jobs", [])
                            
                            for item in job_items:
                                job = self._parse_api_job(item)
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
            log.debug(f"API scraping failed, trying HTML: {str(e)}")
        
        return [], False

    def _scrape_page_html(self, page: int) -> tuple[list[JobPost], bool]:
        """
        Scrapes jobs from HTML page
        Note: sg.jora.com is protected by Cloudflare, so HTML scraping may not work
        without JavaScript execution or Cloudflare bypass.
        """
        try:
            # Jora uses 'q' for query and 'l' for location
            params = {
                "q": self.scraper_input.search_term or "",
            }
            
            if self.scraper_input.location:
                params["l"] = self.scraper_input.location
            
            if page > 1:
                params["page"] = page

            response = self.session.get(self.search_url, params=params, timeout=10)
            
            # Check for Cloudflare challenge
            if response.status_code == 403 or "Just a moment" in response.text or "challenge-platform" in response.text:
                log.warning("Cloudflare protection detected. HTML scraping may not work without JavaScript execution.")
                return [], False
            
            if response.status_code != 200:
                return [], False

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find job listings in HTML
            jobs = []
            
            # Look for embedded JSON data (JobsDB uses React)
            script_tags = soup.find_all("script", type="application/json")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if "results" in data or "jobs" in data or "jobList" in data:
                        job_items = data.get("results", []) or data.get("jobs", []) or data.get("jobList", [])
                        for item in job_items:
                            job = self._parse_json_job(item)
                            if job:
                                jobs.append(job)
                        break
                except:
                    continue
            
            # If no JSON found, try parsing HTML directly
            if not jobs:
                # Look for job card elements - Jora/Seek structure
                # Try common selectors for job listings
                job_selectors = [
                    ("article", {"data-automation": lambda x: x and "jobCard" in x}),
                    ("div", {"class": lambda c: c and "job" in (c or "").lower()}),
                    ("div", {"data-testid": lambda x: x and "job" in (x or "").lower()}),
                ]
                
                for tag_name, attrs in job_selectors:
                    job_cards = soup.find_all(tag_name, attrs)
                    if job_cards:
                        for card in job_cards:
                            job = self._parse_html_job(card)
                            if job:
                                jobs.append(job)
                        if jobs:
                            break
            
            has_more = len(jobs) == self.jobs_per_page
            return jobs, has_more

        except Exception as e:
            log.error(f"HTML scraping error: {str(e)}")
            return [], False

    def _parse_api_job(self, item: dict) -> Optional[JobPost]:
        """Parse job from API response"""
        try:
            job_id = item.get("id") or item.get("jobId") or item.get("job_id") or f"jobsdb-{hash(item.get('url', ''))}"
            title = item.get("title") or item.get("jobTitle") or item.get("job_title", "N/A")
            company = item.get("company") or item.get("companyName") or item.get("company_name", "N/A")
            location_text = item.get("location") or item.get("jobLocation") or item.get("job_location", "Singapore")
            job_url = item.get("url") or item.get("jobUrl") or item.get("job_url")
            
            if job_url and not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)
            elif not job_url:
                # Jora uses different URL structure
                if job_id:
                    job_url = f"{self.base_url}/viewjob?jk={job_id}"
                else:
                    job_url = f"{self.base_url}/j/{job_id}"

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
                id=f"jobsdb-{job_id}",
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

    def _parse_json_job(self, item: dict) -> Optional[JobPost]:
        """Parse job from embedded JSON"""
        return self._parse_api_job(item)

    def _parse_html_job(self, card) -> Optional[JobPost]:
        """Parse job from HTML card"""
        try:
            # Find job link
            link = card.find("a", href=True)
            if not link:
                return None

            job_url = link.get("href")
            if not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)

            # Extract title
            title = link.get_text(strip=True) or "N/A"
            
            # Extract company
            company_elem = card.find(["span", "div"], class_=lambda c: c and "company" in (c or "").lower())
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            # Extract location
            location_elem = card.find(["span", "div"], class_=lambda c: c and "location" in (c or "").lower())
            location_text = location_elem.get_text(strip=True) if location_elem else "Singapore"
            location = parse_location(location_text)

            # Extract date
            date_elem = card.find(["span", "div"], class_=lambda c: c and "date" in (c or "").lower())
            date_posted = None
            if date_elem:
                date_posted = parse_date(date_elem.get_text(strip=True))

            return JobPost(
                id=f"jobsdb-{hash(job_url)}",
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
