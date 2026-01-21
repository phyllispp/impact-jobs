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
from jobspy.mcareersfuture.constant import headers
from jobspy.mcareersfuture.util import parse_location, parse_date, is_job_remote

log = create_logger("MyCareersFuture")


class MyCareersFuture(Scraper):
    base_url = "https://www.mycareersfuture.gov.sg"
    search_url = "https://www.mycareersfuture.gov.sg/search"
    delay = 2
    band_delay = 3
    jobs_per_page = 20

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        """
        Initializes MyCareersFuture scraper
        """
        super().__init__(Site.MYCAREERSFUTURE, proxies=proxies, ca_cert=ca_cert)
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
        Scrapes MyCareersFuture for jobs with scraper_input criteria
        """
        self.scraper_input = scraper_input
        job_list: list[JobPost] = []
        page = 0
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
            api_url = "https://api.mycareersfuture.gov.sg/v2/jobs"
            
            params = {
                "search": self.scraper_input.search_term or "",
                "page": page,
                "limit": self.jobs_per_page,
            }
            
            if self.scraper_input.location:
                # MyCareersFuture uses location filters differently
                params["location"] = self.scraper_input.location
            
            if self.scraper_input.hours_old:
                # Calculate date filter - API uses days
                days_ago = int(self.scraper_input.hours_old / 24)
                params["postedDate"] = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    jobs = []
                    
                    # Parse API response - structure is {"results": [...]}
                    job_items = data.get("results", [])
                    
                    for item in job_items:
                        job = self._parse_api_job(item)
                        if job:
                            jobs.append(job)
                    
                    # Check if there are more pages
                    has_more = len(job_items) == self.jobs_per_page
                    return jobs, has_more
                except json.JSONDecodeError as e:
                    log.debug(f"JSON decode error: {e}")
        except Exception as e:
            log.debug(f"API scraping failed: {str(e)}")
        
        return [], False

    def _scrape_page_html(self, page: int) -> tuple[list[JobPost], bool]:
        """
        Scrapes jobs from HTML page
        """
        try:
            params = {
                "search": self.scraper_input.search_term or "",
                "page": page,
            }
            
            if self.scraper_input.location:
                params["location"] = self.scraper_input.location

            response = self.session.get(self.search_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return [], False

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find job listings in HTML
            # MyCareersFuture uses React, so we may need to parse JSON data embedded in page
            jobs = []
            
            # Look for embedded JSON data
            script_tags = soup.find_all("script", type="application/json")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if "results" in data or "jobs" in data:
                        job_items = data.get("results", []) or data.get("jobs", [])
                        for item in job_items:
                            job = self._parse_json_job(item)
                            if job:
                                jobs.append(job)
                        break
                except:
                    continue
            
            # If no JSON found, try parsing HTML directly
            if not jobs:
                job_cards = soup.find_all(["div", "article"], class_=lambda c: c and "job" in (c or "").lower())
                for card in job_cards:
                    job = self._parse_html_job(card)
                    if job:
                        jobs.append(job)
            
            has_more = len(jobs) == self.jobs_per_page
            return jobs, has_more

        except Exception as e:
            log.error(f"HTML scraping error: {str(e)}")
            return [], False

    def _parse_api_job(self, item: dict) -> Optional[JobPost]:
        """Parse job from API response"""
        try:
            # Extract job ID (uuid)
            job_id = item.get("uuid") or f"mcf-{hash(str(item))}"
            
            # Extract title
            title = item.get("title", "N/A")
            
            # Extract company name
            posted_company = item.get("postedCompany", {})
            company = posted_company.get("name", "N/A")
            
            # Extract location from address
            address = item.get("address", {})
            location_parts = []
            if address.get("building"):
                location_parts.append(address["building"])
            if address.get("street"):
                location_parts.append(address["street"])
            if address.get("postalCode"):
                location_parts.append(address["postalCode"])
            location_text = ", ".join(location_parts) if location_parts else "Singapore"
            
            # Get job URL from metadata
            metadata = item.get("metadata", {})
            job_url = metadata.get("jobDetailsUrl")
            if not job_url:
                job_url = f"{self.base_url}/job/{job_id}"

            # Parse date from metadata
            date_posted = None
            date_str = metadata.get("newPostingDate") or metadata.get("originalPostingDate")
            if date_str:
                try:
                    date_posted = datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    pass

            # Parse location
            location = parse_location(location_text)

            # Get description (HTML format)
            description = item.get("description", "")
            
            # Extract salary if available
            compensation = None
            salary = item.get("salary", {})
            if salary.get("minimum") and salary.get("maximum"):
                from jobspy.model import Compensation, CompensationInterval
                compensation = Compensation(
                    min_amount=float(salary["minimum"]),
                    max_amount=float(salary["maximum"]),
                    currency="SGD",
                    interval=CompensationInterval.MONTHLY if salary.get("type", {}).get("id") == 4 else CompensationInterval.YEARLY
                )

            return JobPost(
                id=f"mcf-{job_id}",
                title=title,
                company_name=company,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                description=description,
                compensation=compensation,
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
                id=f"mcf-{hash(job_url)}",
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
