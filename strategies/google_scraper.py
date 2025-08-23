#!/usr/bin/env python3
"""
Google Scraper Module
Google search result scraper for testing purposes.
"""

import time
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from dotenv import load_dotenv

from .base_scraper import BaseScraper, ScrapedContent
from database.database import DatabaseManager
from config.config import (
    find_chrome_driver,
    find_chrome_binary,
    load_chrome_config_from_env,
)

# Load environment variables
load_dotenv()


@dataclass
class GoogleSearchResult(ScrapedContent):
    """Google search result data model."""

    # Override base class fields with defaults
    content: str
    url: str
    scraped_at: str
    title: str = ""
    snippet: str = ""
    position: int = 0
    # Optional fields with defaults
    content_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GoogleScraper(BaseScraper):
    """Google search result scraper for testing purposes."""

    def __init__(self, db_path: str = "google_search_results.db"):
        super().__init__(name="GoogleScraper")
        self.ua = UserAgent()
        self.db_manager = DatabaseManager(db_path)
        self.search_results = []

    def setup_driver(self, headless: bool = True) -> bool:
        """Setup Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()

            # Load configuration from config.py
            config = load_chrome_config_from_env()

            # Set headless mode
            if headless:
                chrome_options.add_argument("--headless")

            # Apply Chrome options from config
            if config["no_sandbox"]:
                chrome_options.add_argument("--no-sandbox")
            if config["disable_dev_shm_usage"]:
                chrome_options.add_argument("--disable-dev-shm-usage")
            if config["disable_gpu"]:
                chrome_options.add_argument("--disable-gpu")
            if config["window_size"]:
                chrome_options.add_argument(f"--window-size={config['window_size']}")
            if config["disable_blink_features"]:
                chrome_options.add_argument(
                    f"--disable-blink-features={config['disable_blink_features']}"
                )
            if config["exclude_switches"]:
                chrome_options.add_experimental_option(
                    "excludeSwitches", config["exclude_switches"]
                )
            if not config["use_automation_extension"]:
                chrome_options.add_experimental_option("useAutomationExtension", False)

            # Set user agent
            chrome_options.add_argument(f"--user-agent={self.ua.random}")

            # Find Chrome driver and binary paths
            driver_path = find_chrome_driver()
            binary_path = find_chrome_binary()

            # Set Chrome binary location if found
            if binary_path:
                chrome_options.binary_location = binary_path

            # Create service with found driver path or fallback to webdriver_manager
            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Fallback to webdriver_manager if no local driver found
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set window size
            self.driver.set_window_size(1920, 1080)

            # Execute script to remove webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self.logger.info("Chrome WebDriver setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup driver: {str(e)}")
            return False

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Google (not required for public search)."""
        # Google search doesn't require authentication for basic searches
        self.is_authenticated = True
        self.logger.info(
            "Google scraper doesn't require authentication for basic searches"
        )
        return True

    def validate_target_url(self, url: str) -> bool:
        """Validate if the target URL is a Google search URL."""
        return "google.com" in url.lower() or "google.co" in url.lower()

    def pre_scraping_setup(self, target_url: str) -> bool:
        """Navigate to Google search page."""
        try:
            if not self.driver:
                self.logger.error("Driver not initialized")
                return False

            # Navigate to Google
            self.driver.get("https://www.google.com")
            time.sleep(2)

            # Accept cookies if the dialog appears
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(text(), 'Accept all') or contains(text(), 'I agree')]",
                        )
                    )
                )
                cookie_button.click()
                time.sleep(1)
            except Exception:
                self.logger.info("No cookie dialog found or already accepted")

            return True

        except Exception as e:
            self.logger.error(f"Failed to setup Google page: {str(e)}")
            return False

    def scrape_search_results(
        self, target_url: str, max_results: int = 20
    ) -> List[ScrapedContent]:
        """Scrape Google search results."""
        try:
            if not self.pre_scraping_setup(target_url):
                return []

            # Extract search query from URL or use default
            search_query = self._extract_search_query(target_url) or "test search"

            # Perform search
            if not self.driver:
                self.logger.error("Driver not initialized")
                return []

            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)

            # Wait for results to load
            time.sleep(3)

            # Scroll to load more results if needed
            self._scroll_for_more_results(max_results)

            # Extract search results
            search_results = self._extract_search_results(max_results)

            # Convert to GoogleSearchResult format
            results = []
            for i, result in enumerate(search_results):
                search_result = GoogleSearchResult(
                    content=result.get("snippet", ""),
                    url=result.get("url", ""),
                    scraped_at=datetime.now().isoformat(),
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    position=i + 1,
                    metadata={
                        "search_query": search_query,
                        "result_position": i + 1,
                        "result_type": "search_result",
                    },
                )
                results.append(search_result)

            self.logger.info(f"Successfully scraped {len(results)} Google search results")
            return results

        except Exception as e:
            self.logger.error(f"Failed to scrape Google search results: {str(e)}")
            return []

    def _extract_search_query(self, url: str) -> Optional[str]:
        """Extract search query from Google search URL."""
        try:
            if "google.com/search" in url:
                # Extract query parameter
                match = re.search(r"[?&]q=([^&]+)", url)
                if match:
                    return match.group(1).replace("+", " ")
            return None
        except Exception as e:
            self.logger.error(f"Failed to extract search query: {str(e)}")
            return None

    def _scroll_for_more_results(self, max_results: int):
        """Scroll down to load more search results."""
        if not self.driver:
            self.logger.error("Driver not initialized")
            return

        try:
            current_results = 0
            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            while current_results < max_results:
                # Scroll down
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)

                # Count current results
                current_results = len(
                    self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                )

                # Check if we've reached the bottom
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height

                if current_results >= max_results:
                    break

        except Exception as e:
            self.logger.error(f"Failed to scroll for more results: {str(e)}")

    def _extract_search_results(self, max_results: int) -> List[Dict[str, str]]:
        """Extract search results from the page."""
        if not self.driver:
            self.logger.error("Driver not initialized")
            return []

        try:
            results = []
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

            for element in result_elements[:max_results]:
                try:
                    # Extract title
                    title_element = element.find_element(By.CSS_SELECTOR, "h3")
                    title = title_element.text if title_element else ""

                    # Extract URL
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    url = link_element.get_attribute("href") if link_element else ""

                    # Extract snippet
                    snippet_element = element.find_element(
                        By.CSS_SELECTOR, "div.VwiC3b"
                    )
                    snippet = snippet_element.text if snippet_element else ""

                    # Extract author/source (from URL)
                    if url:
                        author = self._extract_domain_from_url(url)
                    else:
                        author = "Unknown"

                    results.append(
                        {
                            "title": title,
                            "url": url or "",
                            "snippet": snippet,
                            "author": author,
                        }
                    )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to extract individual result: {str(e)}"
                    )
                    continue

            return results

        except Exception as e:
            self.logger.error(f"Failed to extract search results: {str(e)}")
            return []

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            import urllib.parse

            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return "Unknown"

    def search_and_scrape(
        self, query: str, max_results: int = 20
    ) -> List[ScrapedContent]:
        """Convenience method to perform search and scrape results."""
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.scrape_search_results(search_url, max_results)

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about the scraping session."""
        stats = super().get_scraping_stats()
        stats.update(
            {
                "total_results_scraped": len(self.search_results),
                "driver_status": "active" if self.driver else "inactive",
            }
        )
        return stats

    def scrape_content(self, target_url: str, max_items: int = 20) -> List[ScrapedContent]:
        """Scrape content from the target URL - implements abstract method."""
        return self.scrape_search_results(target_url, max_items)

    def extract_content_data(self, content_element) -> Optional[ScrapedContent]:
        """Extract data from a single content element - implements abstract method."""
        try:
            # This is a placeholder implementation for the abstract method
            # The actual extraction is done in _extract_search_results
            return None
        except Exception as e:
            self.logger.error(f"Error extracting content data: {str(e)}")
            return None

    def scrape_posts(self, target_url: str, max_posts: int = 20) -> List[ScrapedContent]:
        """Alias for scrape_content to maintain compatibility with main.py."""
        return self.scrape_content(target_url, max_posts)

    def save_posts_to_database(self, posts: List[ScrapedContent]) -> int:
        """Save scraped posts to the database using DatabaseManager."""
        if not posts:
            return 0

        # Convert ScrapedContent objects to dictionaries
        posts_data = []
        for post in posts:
            posts_data.append({
                'content': post.content,
                'url': post.url,
                'scraped_at': post.scraped_at,
                'title': getattr(post, 'title', ''),
                'snippet': getattr(post, 'snippet', ''),
                'position': getattr(post, 'position', 0),
                'metadata': post.metadata or {}
            })

        return self.db_manager.save_posts(posts_data)

    def save_posts_to_json(self, posts: List[ScrapedContent], filename: str = "google_search_results.json") -> bool:
        """Save scraped posts to a JSON file."""
        try:
            posts_data = []
            for post in posts:
                posts_data.append({
                    'content': post.content,
                    'url': post.url,
                    'scraped_at': post.scraped_at,
                    'title': getattr(post, 'title', ''),
                    'snippet': getattr(post, 'snippet', ''),
                    'position': getattr(post, 'position', 0),
                    'metadata': post.metadata or {}
                })

            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(posts_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(posts)} search results to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving search results to JSON: {str(e)}")
            return False

    def monitor_group(self, group_url: str, interval_minutes: int = 30, max_posts: int = 20):
        """Monitor group (not applicable for Google scraper)."""
        self.logger.warning("Continuous monitoring is not supported for Google scraper")
        return []

    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        super().close()
