#!/usr/bin/env python3
"""
Base Scraper Module
Abstract base class for all scraper implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ScrapedContent:
    """Base data class for scraped content information."""
    content: str                      # Main content text
    url: str                          # URL of the scraped content
    scraped_at: str                  # When the content was scraped
    content_id: Optional[str] = None  # Optional ID if the website provides one
    title: Optional[str] = None       # Optional title for the content
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata specific to the content type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'content': self.content,
            'url': self.url,
            'scraped_at': self.scraped_at,
            'content_id': self.content_id,
            'title': self.title,
            'metadata': self.metadata or {}
        }


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, name: str = "BaseScraper"):
        self.name = name
        self.logger = self._setup_logger()
        self.driver = None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the scraper."""
        logger = logging.getLogger(f"{__name__}.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @abstractmethod
    def setup_driver(self, **kwargs) -> bool:
        """Setup the web driver for scraping."""
        pass

    @abstractmethod
    def scrape_content(self, target_url: str, max_items: int = 20) -> List[ScrapedContent]:
        """Scrape content from the target URL."""
        pass

    @abstractmethod
    def extract_content_data(self, content_element) -> Optional[ScrapedContent]:
        """Extract data from a single content element."""
        pass

    def validate_target_url(self, url: str) -> bool:
        """Validate if the target URL is supported by this scraper."""
        return True

    def pre_scraping_setup(self, target_url: str) -> bool:
        """Perform any necessary setup before scraping."""
        return True

    def post_scraping_cleanup(self) -> bool:
        """Perform any necessary cleanup after scraping."""
        return True

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about the scraping session."""
        return {
            "scraper_name": self.name,
            "timestamp": self._get_current_timestamp()
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
        self.logger.info(f"Closing {self.name}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
