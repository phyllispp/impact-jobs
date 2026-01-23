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
from jobspy.ctgoodjobs.constant import headers
from jobspy.ctgoodjobs.util import parse_location, parse_date, is_job_remote

log = create_logger("CTgoodjobs")


class CTgoodjobs(Scraper):
    base_url = "https://www.ctgoodjobs.hk"
    search_url = "https://jobs.ctgoodjobs.hk/jobs"
    delay = 2
    band_delay = 3
    jobs_per_page = 20

    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None, user_agent: str | None = None
    ):
        """
        Initializes CTgoodjobs scraper
        """
        super().__init__(Site.CTGOODJOBS, proxies=proxies, ca_cert=ca_cert)
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
        Scrapes CTgoodjobs for jobs with scraper_input criteria
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
            # CTgoodjobs might have an API endpoint
            search_term = (self.scraper_input.search_term or "").strip().lower().replace(" ", "-")
            api_urls = [
                f"{self.base_url}/api/jobs",
                f"{self.search_url}/api/search",
                f"https://jobs.ctgoodjobs.hk/api/v1/jobs",
            ]
            
            params = {
                "q": self.scraper_input.search_term or "",
                "page": page,
                "limit": self.jobs_per_page,
            }

            for api_url in api_urls:
                try:
                    response = self.session.get(api_url, params=params, timeout=10)
                    
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
            log.debug(f"API scraping failed, trying HTML: {str(e)}")
        
        return [], False

    def _scrape_page_html(self, page: int) -> tuple[list[JobPost], bool]:
        """
        Scrapes jobs from HTML page
        """
        try:
            # CTgoodjobs uses URL pattern: https://jobs.ctgoodjobs.hk/jobs/{search-term}-jobs
            search_term = (self.scraper_input.search_term or "").strip().lower().replace(" ", "-")
            
            if not search_term:
                return [], False
            
            if page == 1:
                url = f"{self.search_url}/{search_term}-jobs"
            else:
                url = f"{self.search_url}/{search_term}-jobs?page={page}"

            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return [], False

            soup = BeautifulSoup(response.text, "html.parser")
            jobs = []
            
            # Look for embedded JSON data (React apps often embed data)
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
            # Note: CTgoodjobs is a React app, so jobs may be loaded dynamically
            # We'll try to find any server-rendered content or use a headless browser approach
            if not jobs:
                # Look for job card elements - exclude skeleton/loading cards
                job_cards = soup.find_all("div", class_=lambda c: c and "job-card" in str(c) if c else False)
                
                # Filter out skeleton cards
                real_job_cards = [
                    card for card in job_cards 
                    if "skeleton" not in str(card.get("class", [])).lower()
                ]
                
                if real_job_cards:
                    log.info(f"Found {len(real_job_cards)} job cards (excluding skeletons)")
                    for card in real_job_cards[:self.jobs_per_page]:
                        job = self._parse_html_job(card)
                        if job and job.title != "N/A" and "alert" not in job.title.lower():
                            jobs.append(job)
                
                # If still no jobs, try finding links that might be job links
                if not jobs:
                    # Look for links in the main content area
                    main_content = soup.find(["main", "div"], id=lambda i: i and ("content" in str(i).lower() or "main" in str(i).lower()) if i else False)
                    search_area = main_content if main_content else soup
                    
                    all_links = search_area.find_all("a", href=True)
                    for link in all_links:
                        href = link.get("href", "")
                        text = link.get_text(strip=True)
                        
                        # Look for job links - exclude navigation links
                        if (("/job/" in href.lower() or 
                             href.startswith("/jobs/") or
                             (search_term in href.lower() and len(text) > 10)) and
                            "alert" not in text.lower() and
                            "create" not in text.lower()):
                            job = self._parse_html_job_from_link(link)
                            if job and job.title != "N/A":
                                jobs.append(job)
                                if len(jobs) >= self.jobs_per_page:
                                    break
                
                # If still no jobs, the page likely loads jobs via JavaScript
                # Log a warning that we need JavaScript execution
                if not jobs:
                    log.warning("CTgoodjobs appears to load jobs dynamically via JavaScript. Consider using a headless browser (Selenium/Playwright) for full functionality.")
            
            has_more = len(jobs) == self.jobs_per_page
            return jobs, has_more

        except Exception as e:
            log.error(f"HTML scraping error: {str(e)}")
            return [], False

    def _parse_api_job(self, item: dict) -> Optional[JobPost]:
        """Parse job from API response"""
        try:
            job_id = item.get("id") or item.get("jobId") or item.get("job_id") or f"ctgoodjobs-{hash(str(item))}"
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
                id=f"ctgoodjobs-{job_id}",
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
            # Skip skeleton/loading cards
            if card.get("class") and "skeleton" in str(card.get("class")).lower():
                return None
            
            # Find job link - try multiple approaches
            link = card.find("a", href=True)
            if not link:
                # Maybe the card itself is a link
                if card.name == "a" and card.get("href"):
                    link = card
                else:
                    return None

            job_url = link.get("href")
            if not job_url or job_url == "#":
                return None
                
            if not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)

            # Extract title - try multiple selectors
            title = "N/A"
            title_selectors = [
                link.find(["h1", "h2", "h3", "h4", "h5", "h6"]),
                link.find(["span", "div"], class_=lambda c: c and "title" in str(c).lower() if c else False),
                card.find(["h1", "h2", "h3", "h4", "h5", "h6"]),
                card.find(["span", "div"], class_=lambda c: c and "title" in str(c).lower() if c else False),
            ]
            
            for title_elem in title_selectors:
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:  # Valid title
                        break
            
            # Fallback to link text
            if not title or title == "N/A" or len(title) < 5:
                title = link.get_text(strip=True)
            
            # Filter out invalid titles
            if not title or len(title) < 5 or "alert" in title.lower() or "create" in title.lower():
                return None
            
            # Extract company
            company = "N/A"
            company_selectors = [
                card.find(["span", "div", "a"], class_=lambda c: c and "company" in str(c).lower() if c else False),
                card.find(["span", "div"], class_=lambda c: c and "employer" in str(c).lower() if c else False),
            ]
            
            for company_elem in company_selectors:
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    if company and len(company) > 1:
                        break

            # Extract location
            location_text = "Hong Kong"
            location_selectors = [
                card.find(["span", "div"], class_=lambda c: c and "location" in str(c).lower() if c else False),
                card.find(["span", "div"], class_=lambda c: c and "area" in str(c).lower() if c else False),
            ]
            
            for location_elem in location_selectors:
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text:
                        break
            
            location = parse_location(location_text)

            # Extract date
            date_posted = None
            date_selectors = [
                card.find(["span", "div"], class_=lambda c: c and "date" in str(c).lower() if c else False),
                card.find(["span", "div"], class_=lambda c: c and "time" in str(c).lower() if c else False),
                card.find(["span", "div"], class_=lambda c: c and "posted" in str(c).lower() if c else False),
            ]
            
            for date_elem in date_selectors:
                if date_elem:
                    date_posted = parse_date(date_elem.get_text(strip=True))
                    if date_posted:
                        break

            return JobPost(
                id=f"ctgoodjobs-{hash(job_url)}",
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

    def _parse_html_job_from_link(self, link) -> Optional[JobPost]:
        """Parse job from a link element"""
        try:
            job_url = link.get("href")
            if not job_url.startswith("http"):
                job_url = urljoin(self.base_url, job_url)

            title = link.get_text(strip=True) or "N/A"
            
            # Try to find parent container for more info
            parent = link.find_parent(["div", "article", "li"])
            company = "N/A"
            location_text = "Hong Kong"
            
            if parent:
                company_elem = parent.find(["span", "div"], class_=lambda c: c and "company" in str(c).lower() if c else False)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                
                location_elem = parent.find(["span", "div"], class_=lambda c: c and "location" in str(c).lower() if c else False)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)

            location = parse_location(location_text)

            return JobPost(
                id=f"ctgoodjobs-{hash(job_url)}",
                title=title,
                company_name=company,
                location=location,
                job_url=job_url,
                is_remote=is_job_remote(title, location=location),
            )
        except Exception as e:
            log.error(f"Error parsing job from link: {str(e)}")
            return None
