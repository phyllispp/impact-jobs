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
from jobspy.jobsdb_hk.constant import headers
from jobspy.jobsdb_hk.util import parse_location, parse_date, is_job_remote

log = create_logger("JobsDB_HK")


class JobsDBHK(Scraper):
    base_url = "https://hk.jobsdb.com"
    search_url = "https://hk.jobsdb.com/jobs"
    delay = 2
    band_delay = 3
    jobs_per_page = 20

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        """
        Initializes JobsDB Hong Kong scraper
        Note: JobsDB HK is protected by Cloudflare and may require JavaScript execution
        """
        super().__init__(Site.JOBSDB_HK, proxies=proxies, ca_cert=ca_cert)
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
        Scrapes JobsDB HK for jobs with scraper_input criteria
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
            api_urls = [
                f"{self.base_url}/api/chalice-search/v4/search",
                f"{self.base_url}/api/job-search",
            ]
            
            params = {
                "q": self.scraper_input.search_term or "",
                "page": page,
                "pageSize": self.jobs_per_page,
            }

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
            log.debug(f"API scraping failed: {str(e)}")
        
        return [], False

    def _scrape_page_html(self, page: int) -> tuple[list[JobPost], bool]:
        """
        Scrapes jobs from HTML page
        Note: JobsDB HK is protected by Cloudflare, so HTML scraping may not work
        without JavaScript execution or Cloudflare bypass.
        """
        try:
            # JobsDB HK uses URL pattern: https://hk.jobsdb.com/jobs/{search-term}
            search_term = (self.scraper_input.search_term or "").strip().lower().replace(" ", "-")
            
            if not search_term:
                return [], False
            
            if page == 1:
                url = f"{self.search_url}/{search_term}"
            else:
                url = f"{self.search_url}/{search_term}?page={page}"

            response = self.session.get(url, timeout=10)
            
            # Check for Cloudflare challenge
            if response.status_code == 403 or "Just a moment" in response.text or "challenge-platform" in response.text:
                log.warning("Cloudflare protection detected. JobsDB HK HTML scraping requires JavaScript execution or Cloudflare bypass.")
                return [], False
            
            if response.status_code != 200:
                return [], False

            soup = BeautifulSoup(response.text, "html.parser")
            jobs = []
            
            # Look for embedded JSON data
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
                job_selectors = [
                    ("article", {"data-automation": lambda x: x and "jobCard" in str(x) if x else False}),
                    ("div", {"class": lambda c: c and "job" in str(c).lower() if c else False}),
                ]
                
                for tag_name, attrs in job_selectors:
                    try:
                        job_cards = soup.find_all(tag_name, attrs)
                        if job_cards:
                            for card in job_cards:
                                job = self._parse_html_job(card)
                                if job:
                                    jobs.append(job)
                            if jobs:
                                break
                    except:
                        continue
            
            has_more = len(jobs) == self.jobs_per_page
            return jobs, has_more

        except Exception as e:
            log.error(f"HTML scraping error: {str(e)}")
            return [], False

    def _parse_api_job(self, item: dict) -> Optional[JobPost]:
        """Parse job from API response"""
        try:
            job_id = item.get("id") or item.get("jobId") or item.get("job_id") or f"jobsdb-hk-{hash(str(item))}"
            title = item.get("title") or item.get("jobTitle") or item.get("job_title", "N/A")
            company = item.get("company") or item.get("companyName") or item.get("company_name", "N/A")
            location_text = item.get("location") or item.get("jobLocation") or item.get("job_location", "Hong Kong")
            job_url = item.get("url") or item.get("jobUrl") or item.get("job_url")
            
            if job_url and not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)
            elif not job_url:
                job_url = f"{self.base_url}/job/{job_id}" if job_id else f"{self.base_url}/jobs/{job_id}"

            date_posted = None
            date_str = item.get("postedDate") or item.get("datePosted") or item.get("posted_date")
            if date_str:
                date_posted = parse_date(date_str)

            location = parse_location(location_text)
            description = item.get("description") or item.get("jobDescription") or item.get("job_description", "")

            return JobPost(
                id=f"jobsdb-hk-{job_id}",
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
            link = card.find("a", href=True)
            if not link:
                return None

            job_url = link.get("href")
            if not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)

            title = link.get_text(strip=True) or "N/A"
            
            company_elem = card.find(["span", "div"], class_=lambda c: c and "company" in str(c).lower() if c else False)
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = card.find(["span", "div"], class_=lambda c: c and "location" in str(c).lower() if c else False)
            location_text = location_elem.get_text(strip=True) if location_elem else "Hong Kong"
            location = parse_location(location_text)

            date_elem = card.find(["span", "div"], class_=lambda c: c and "date" in str(c).lower() if c else False)
            date_posted = None
            if date_elem:
                date_posted = parse_date(date_elem.get_text(strip=True))

            return JobPost(
                id=f"jobsdb-hk-{hash(job_url)}",
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
