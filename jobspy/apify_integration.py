"""
Apify integration for scraping Jobstreet (Singapore) and JobsDB (Hong Kong)
Uses pay-per-usage actors to stay within free tier limits
"""
from __future__ import annotations

import os
import time
import requests
from typing import Optional, List, Dict
import pandas as pd
from datetime import datetime

from jobspy.model import JobPost, Location, Country, JobResponse
from jobspy.util import create_logger

log = create_logger("ApifyIntegration")

# Apify API configuration
APIFY_API_BASE = "https://api.apify.com/v2"
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")

# Actor IDs for pay-per-usage scrapers
# Seek Job Scraper for JobStreet (websift) - $2.50 per 1,000 results
JOBSTREET_ACTOR_ID = "websift/seek-job-scraper"  # Actor: websift~seek-job-scraper

# JobsDB scraper - need to find pay-per-usage option
# Using Shahid Irfan's scraper as it's pay-per-usage (pricing TBD)
JOBSDB_HK_ACTOR_ID = "shahidirfan/jobsdb-scraper"  # Actor: shahidirfan~jobsdb-scraper


class ApifyJobstreetSG:
    """Apify integration for JobStreet Singapore"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or APIFY_API_TOKEN
        if not self.api_token:
            log.warning("APIFY_API_TOKEN not set. Apify scraping will be disabled.")
    
    def scrape(self, search_term: str, results_wanted: int = 30) -> List[JobPost]:
        """
        Scrape JobStreet Singapore jobs via Apify
        Cost: ~$2.50 per 1,000 results (pay-per-usage)
        """
        if not self.api_token:
            log.warning("Apify API token not configured. Skipping JobStreet scraping.")
            return []
        
        try:
            log.info(f"Scraping JobStreet Singapore via Apify: '{search_term}'")
            
            # Prepare actor input
            # Seek Job Scraper uses: searchTerm, maxResults, suburbOrCity
            actor_input = {
                "searchTerm": search_term,
                "maxResults": min(results_wanted, 550),  # Actor limit is 550
                "suburbOrCity": "Singapore",  # Location filter for Singapore
            }
            
            # Run the actor
            run_id = self._run_actor(JOBSTREET_ACTOR_ID, actor_input)
            if not run_id:
                return []
            
            # Wait for completion and get results
            self._wait_for_completion(run_id)
            jobs = self._get_results(run_id)
            
            log.info(f"Found {len(jobs)} jobs from JobStreet via Apify")
            return jobs
            
        except Exception as e:
            log.error(f"Error scraping JobStreet via Apify: {str(e)}")
            return []
    
    def _run_actor(self, actor_id: str, input_data: Dict) -> Optional[str]:
        """Start an Apify actor run"""
        try:
            url = f"{APIFY_API_BASE}/acts/{actor_id}/runs"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(url, json=input_data, headers=headers, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                run_id = data["data"]["id"]
                log.info(f"Actor run started: {run_id}")
                return run_id
            else:
                log.error(f"Failed to start actor: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            log.error(f"Error starting actor run: {str(e)}")
            return None
    
    def _wait_for_completion(self, run_id: str, max_wait: int = 300) -> bool:
        """Wait for actor run to complete"""
        url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()["data"]
                    status = data["status"]
                    
                    if status == "SUCCEEDED":
                        log.info("Actor run completed successfully")
                        return True
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        log.error(f"Actor run {status.lower()}")
                        return False
                    # Still running - continue waiting
                    time.sleep(5)
                else:
                    log.error(f"Error checking run status: {response.status_code}")
                    return False
            except Exception as e:
                log.error(f"Error waiting for completion: {str(e)}")
                return False
        
        log.warning("Actor run timed out")
        return False
    
    def _get_results(self, run_id: str) -> List[JobPost]:
        """Get results from completed actor run"""
        try:
            # Get run details to find dataset ID
            url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                log.error(f"Failed to get run details: {response.status_code}")
                return []
            
            run_data = response.json()["data"]
            dataset_id = run_data.get("defaultDatasetId")
            
            if not dataset_id:
                log.error("No dataset ID found in run")
                return []
            
            # Get dataset items
            dataset_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
            response = requests.get(dataset_url, headers=headers, timeout=10, params={"limit": 1000})
            
            if response.status_code != 200:
                log.error(f"Failed to get dataset items: {response.status_code}")
                return []
            
            items = response.json()["data"]["items"]
            jobs = []
            
            for item in items:
                job = self._parse_jobstreet_item(item)
                if job:
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            log.error(f"Error getting results: {str(e)}")
            return []
    
    def _parse_jobstreet_item(self, item: Dict) -> Optional[JobPost]:
        """Parse a JobStreet job item from Apify results"""
        try:
            title = item.get("title") or item.get("jobTitle") or "N/A"
            company = item.get("company") or item.get("companyName") or "N/A"
            job_url = item.get("url") or item.get("jobUrl") or item.get("link") or ""
            location_text = item.get("location") or item.get("area") or "Singapore"
            
            # Parse date
            date_posted = None
            date_str = item.get("postedDate") or item.get("datePosted") or item.get("posted")
            if date_str:
                try:
                    # Try parsing various date formats
                    from jobspy.jobstreet.util import parse_date
                    date_posted = parse_date(date_str)
                except:
                    pass
            
            # Parse location
            location = Location(
                city=location_text.split(",")[0].strip() if location_text else "Singapore",
                country=Country.SINGAPORE
            )
            
            # Get description
            description = item.get("description") or item.get("jobDescription") or ""
            
            return JobPost(
                id=f"apify-jobstreet-{hash(job_url)}",
                title=title,
                company_name=company,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                description=description,
                is_remote="remote" in (title + description).lower(),
            )
        except Exception as e:
            log.error(f"Error parsing job item: {str(e)}")
            return None


class ApifyJobsDBHK:
    """Apify integration for JobsDB Hong Kong"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or APIFY_API_TOKEN
        if not self.api_token:
            log.warning("APIFY_API_TOKEN not set. Apify scraping will be disabled.")
    
    def scrape(self, search_term: str, results_wanted: int = 30) -> List[JobPost]:
        """
        Scrape JobsDB Hong Kong jobs via Apify
        Cost: Pay-per-usage (exact pricing TBD)
        """
        if not self.api_token:
            log.warning("Apify API token not configured. Skipping JobsDB scraping.")
            return []
        
        try:
            log.info(f"Scraping JobsDB Hong Kong via Apify: '{search_term}'")
            
            # Prepare actor input
            # JobsDB scraper input format (may vary - adjust based on actual actor)
            actor_input = {
                "searchQuery": search_term,
                "location": "Hong Kong",
                "maxResults": min(results_wanted, 1000),  # Limit to stay within free tier
            }
            
            # Run the actor
            run_id = self._run_actor(JOBSDB_HK_ACTOR_ID, actor_input)
            if not run_id:
                return []
            
            # Wait for completion and get results
            self._wait_for_completion(run_id)
            jobs = self._get_results(run_id)
            
            log.info(f"Found {len(jobs)} jobs from JobsDB via Apify")
            return jobs
            
        except Exception as e:
            log.error(f"Error scraping JobsDB via Apify: {str(e)}")
            return []
    
    def _run_actor(self, actor_id: str, input_data: Dict) -> Optional[str]:
        """Start an Apify actor run"""
        try:
            url = f"{APIFY_API_BASE}/acts/{actor_id}/runs"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(url, json=input_data, headers=headers, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                run_id = data["data"]["id"]
                log.info(f"Actor run started: {run_id}")
                return run_id
            else:
                log.error(f"Failed to start actor: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            log.error(f"Error starting actor run: {str(e)}")
            return None
    
    def _wait_for_completion(self, run_id: str, max_wait: int = 300) -> bool:
        """Wait for actor run to complete"""
        url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()["data"]
                    status = data["status"]
                    
                    if status == "SUCCEEDED":
                        log.info("Actor run completed successfully")
                        return True
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        log.error(f"Actor run {status.lower()}")
                        return False
                    # Still running - continue waiting
                    time.sleep(5)
                else:
                    log.error(f"Error checking run status: {response.status_code}")
                    return False
            except Exception as e:
                log.error(f"Error waiting for completion: {str(e)}")
                return False
        
        log.warning("Actor run timed out")
        return False
    
    def _get_results(self, run_id: str) -> List[JobPost]:
        """Get results from completed actor run"""
        try:
            # Get run details to find dataset ID
            url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                log.error(f"Failed to get run details: {response.status_code}")
                return []
            
            run_data = response.json()["data"]
            dataset_id = run_data.get("defaultDatasetId")
            
            if not dataset_id:
                log.error("No dataset ID found in run")
                return []
            
            # Get dataset items
            dataset_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
            response = requests.get(dataset_url, headers=headers, timeout=10, params={"limit": 1000})
            
            if response.status_code != 200:
                log.error(f"Failed to get dataset items: {response.status_code}")
                return []
            
            items = response.json()["data"]["items"]
            jobs = []
            
            for item in items:
                job = self._parse_jobsdb_item(item)
                if job:
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            log.error(f"Error getting results: {str(e)}")
            return []
    
    def _parse_jobsdb_item(self, item: Dict) -> Optional[JobPost]:
        """Parse a JobsDB job item from Apify results"""
        try:
            title = item.get("title") or item.get("jobTitle") or "N/A"
            company = item.get("company") or item.get("companyName") or "N/A"
            job_url = item.get("url") or item.get("jobUrl") or item.get("link") or ""
            location_text = item.get("location") or item.get("area") or "Hong Kong"
            
            # Parse date
            date_posted = None
            date_str = item.get("postedDate") or item.get("datePosted") or item.get("posted")
            if date_str:
                try:
                    from jobspy.jobsdb_hk.util import parse_date
                    date_posted = parse_date(date_str)
                except:
                    pass
            
            # Parse location
            location = Location(
                city=location_text.split(",")[0].strip() if location_text else "Hong Kong",
                country=Country.HONGKONG
            )
            
            # Get description
            description = item.get("description") or item.get("jobDescription") or ""
            
            return JobPost(
                id=f"apify-jobsdb-hk-{hash(job_url)}",
                title=title,
                company_name=company,
                location=location,
                date_posted=date_posted,
                job_url=job_url,
                description=description,
                is_remote="remote" in (title + description).lower(),
            )
        except Exception as e:
            log.error(f"Error parsing job item: {str(e)}")
            return None
