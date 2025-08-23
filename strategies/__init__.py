#!/usr/bin/env python3
"""
Strategies package for Facebook Scraper
Contains different scraping strategies and implementations.
"""

from .base_scraper import BaseScraper
from .facebook_scraper import FacebookScraper
from .google_scraper import GoogleScraper

__all__ = [
    "BaseScraper",
    "FacebookScraper",
    "GoogleScraper",
]
