# util.py
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional
import re

from jobspy.model import Location, Country


def parse_location(location_text: str) -> Location:
    """
    Parses location text into a Location object for Singapore
    :param location_text: Location text from job listing
    :return: Location object
    """
    # Singapore locations are typically just city names or "Singapore"
    location_text = location_text.strip()
    if not location_text or location_text.lower() == "singapore":
        return Location(
            city="Singapore",
            country=Country.SINGAPORE
        )
    
    # Try to extract city name
    parts = location_text.split(",")
    city = parts[0].strip()
    
    return Location(
        city=city,
        country=Country.SINGAPORE
    )


def parse_date(date_text: str) -> Optional[datetime]:
    """
    Parses date text into a datetime object
    :param date_text: Date text from job listing
    :return: datetime object or None if parsing fails
    """
    if not date_text:
        return None
    
    try:
        # Common patterns: "2 days ago", "1 week ago", "Posted on 15 Jan 2024"
        date_text = date_text.lower().strip()
        
        # Handle "X days ago" format
        days_match = re.search(r'(\d+)\s*(day|days)\s*ago', date_text)
        if days_match:
            days = int(days_match.group(1))
            return (datetime.now() - timedelta(days=days)).date()
        
        # Handle "X weeks ago" format
        weeks_match = re.search(r'(\d+)\s*(week|weeks)\s*ago', date_text)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return (datetime.now() - timedelta(weeks=weeks)).date()
        
        # Handle "X months ago" format
        months_match = re.search(r'(\d+)\s*(month|months)\s*ago', date_text)
        if months_match:
            months = int(months_match.group(1))
            return (datetime.now() - timedelta(days=months*30)).date()
        
        # Try standard date formats
        date_formats = [
            "%d %b %Y",
            "%d-%b-%Y",
            "%d %B %Y",
            "%B %d, %Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_text, fmt).date()
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def is_job_remote(title: str, description: str = None, location: Location = None) -> bool:
    """
    Determines if a job is remote based on title, description, and location
    """
    remote_keywords = ["remote", "work from home", "wfh", "home based", "work from anywhere"]
    
    full_text = title.lower()
    if description:
        full_text += " " + description.lower()
    
    return any(keyword in full_text for keyword in remote_keywords)
