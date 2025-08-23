#!/usr/bin/env python3
"""
Facebook Scraper Module
Refactored Facebook scraper that inherits from BaseScraper.
"""

import time
import json
import schedule
import re
import random
import os
from typing import List, Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from dotenv import load_dotenv

from .base_scraper import BaseScraper, ScrapedContent

from database.database import DatabaseManager
from database.models import FacebookPost
from config.config import (
    find_chrome_driver,
    find_chrome_binary,
    load_chrome_config_from_env,
)
from utils.chrome_process_manager import ChromeProcessManager
from utils.human_behavior import HumanBehavior

# Load environment variables
load_dotenv()


class FacebookScraper(BaseScraper):
    """Facebook public group post scraper that inherits from BaseScraper."""

    def __init__(self, db_path: str = "facebook_posts.db", fast_mode: bool = False):
        super().__init__(name="FacebookScraper")
        self.ua = UserAgent()
        self.db_manager = DatabaseManager(db_path)
        self.is_authenticated = False
        self.human_behavior = HumanBehavior()
        self.fast_mode = fast_mode  # Enable fast mode for quicker scraping
        self.chrome_manager = ChromeProcessManager(self.logger)

    def setup_driver(
        self, headless: bool = True, use_existing_profile: bool = False
    ) -> bool:
        """Setup Chrome WebDriver with appropriate options."""
        try:
            # Terminate existing Chrome sessions before starting
            self.chrome_manager.terminate_selenium_chrome_sessions()

            chrome_options = Options()

            # Load configuration from config.py
            config = load_chrome_config_from_env()

            # Set headless mode
            if headless:
                chrome_options.add_argument("--headless")

            # Use existing Chrome profile if requested
            if use_existing_profile:
                # Get the default Chrome profile directory for the current user
                import platform

                if platform.system() == "Darwin":  # macOS
                    profile_dir = os.path.expanduser(
                        "~/Library/Application Support/Google/Chrome for Testing/Default"
                    )

                else:  # Linux
                    profile_dir = os.path.expanduser("~/.config/google-chrome/Default")

                if os.path.exists(profile_dir):
                    # Wait for profile directory to be unlocked
                    self.chrome_manager.wait_for_profile_unlock(profile_dir)

                    chrome_options.add_argument(
                        f"--user-data-dir={os.path.dirname(profile_dir)}"
                    )
                    chrome_options.add_argument("--profile-directory=Default")
                    self.logger.info(f"Using existing Chrome profile: {profile_dir}")
                else:
                    self.logger.warning(
                        f"Chrome profile not found at {profile_dir}, using new profile"
                    )

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

            # Apply human-like behavior enhancements
            self.human_behavior.enhance_chrome_options(chrome_options)

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

            # Set driver in human behavior module
            self.human_behavior.set_driver(self.driver)

            # Execute script to remove webdriver property and add human-like properties
            self.human_behavior.remove_automation_flags()

            self.logger.info("Chrome WebDriver setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup driver: {str(e)}")
            return False

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Facebook using provided credentials."""
        try:
            if not self.driver:
                self.logger.error(
                    "WebDriver not initialized. Call setup_driver() first."
                )
                return False

            # First, check if already logged in
            if self._check_if_already_logged_in():
                self.logger.info("Already authenticated with Facebook")
                self.is_authenticated = True
                return True

            email = credentials.get("email")
            password = credentials.get("password")

            if not email or not password:
                self.logger.error("Email and password are required for authentication")
                return False

            self.logger.info("Attempting to login to Facebook...")

            # Navigate to Facebook login page with human-like behavior
            self.human_behavior.natural_page_navigation(
                "https://www.facebook.com/login"
            )

            # Find and fill email field with human-like behavior
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            self.human_behavior.human_fill_form(email_field, email)

            # Pause before moving to password field
            self.human_behavior.random_delay(1, 2)

            # Find and fill password field with human-like behavior
            password_field = self.driver.find_element(By.ID, "pass")
            self.human_behavior.human_fill_form(password_field, password)

            # Pause before clicking login
            self.human_behavior.random_delay(1, 2)

            # Click login button with human-like behavior
            login_button = self.driver.find_element(By.NAME, "login")
            self.human_behavior.human_click(login_button)

            # Wait for login to complete with human-like patience
            self.human_behavior.random_delay(4, 7)

            # Check if login was successful
            if "login" not in self.driver.current_url:
                self.logger.info("Login successful")
                self.is_authenticated = True
                return True
            else:
                self.logger.warning("Login failed - still on login page")
                return False

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    def _check_if_already_logged_in(self) -> bool:
        """Check if the user is already logged into Facebook."""
        try:
            if not self.driver:
                return False

            # Navigate to Facebook homepage to check login status
            self.driver.get("https://www.facebook.com")
            time.sleep(2)

            # Check for elements that indicate user is logged in
            logged_in_indicators = [
                '[data-testid="blue_bar_profile_link"]',  # Profile link in top bar
                '[aria-label="Your profile"]',  # Profile dropdown
                '[data-testid="pagelet_welcome_box"]',  # Welcome box
                '[data-testid="nav_bar_profile"]',  # Navigation profile
            ]

            for selector in logged_in_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.logger.info("Found logged-in indicator: " + selector)
                        return True
                except Exception:
                    continue

            # Also check if we're redirected away from login page
            if (
                "login" not in self.driver.current_url
                and "facebook.com" in self.driver.current_url
            ):
                # Check if there are any login forms visible
                try:
                    login_form = self.driver.find_element(By.ID, "email")
                    if not login_form.is_displayed():
                        self.logger.info(
                            "No login form visible, likely already logged in"
                        )
                        return True
                except Exception:
                    # No login form found, likely logged in
                    self.logger.info("No login form found, likely already logged in")
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking login status: {str(e)}")
            return False

    def validate_target_url(self, url: str) -> bool:
        """Validate if the URL is a Facebook group URL."""
        return "facebook.com/groups/" in url

    def pre_scraping_setup(self, target_url: str) -> bool:
        """Perform setup before scraping."""
        if not self.validate_target_url(target_url):
            self.logger.error(f"Invalid Facebook group URL: {target_url}")
            return False

        if not self.is_authenticated:
            self.logger.warning("Not authenticated with Facebook")

        return True

    def scrape_content(
        self, target_url: str, max_items: int = 20
    ) -> List[FacebookPost]:
        """Scrape posts from a Facebook public group."""
        try:
            if not self.pre_scraping_setup(target_url):
                return []

            if not self.driver:
                self.logger.error(
                    "WebDriver not initialized. Call setup_driver() first."
                )
                return []

            self.logger.info(f"Scraping posts from group: {target_url}")

            # Navigate to group page
            self.driver.get(target_url)
            time.sleep(3)

            # Scroll to load more posts
            self._scroll_to_load_posts(max_items)
            self.logger.info("Successfully scroll to load posts")
            # Find post elements
            posts = self._extract_posts(max_items)

            self.logger.info(f"Successfully scraped {len(posts)} posts")
            return posts

        except Exception as e:
            self.logger.error(f"Error scraping group posts: {str(e)}")
            return []

    def scrape_posts(self, target_url: str, max_posts: int = 20) -> List[FacebookPost]:
        """Alias for scrape_content to maintain compatibility with main.py."""
        return self.scrape_content(target_url, max_posts)

    def extract_content_data(self, post_element) -> Optional[ScrapedContent]:
        """Extract data from a single post element."""
        try:
            # Extract post ID
            post_id = self._extract_post_id(post_element)
            self.logger.info(f"Extracted post ID: {post_id}")
            if not post_id:
                return None

            # Extract author
            author = self._extract_author(post_element)
            self.logger.info(f"Extracted author: {author}")
            if not author:
                return None

            # Extract content
            content = self._extract_post_content(post_element)
            self.logger.info(f"Extracted content length: {len(content) if content else 0} characters")
            if not content:
                return None

            # Extract timestamp
            timestamp = self._extract_timestamp(post_element)
            self.logger.info(f"Extracted timestamp: {timestamp}")

            # Extract post URL
            post_url = self._extract_post_url(post_element)
            self.logger.info(f"Extracted post URL: {post_url}")

            # Extract engagement metrics
            likes_count = self._extract_likes_count(post_element)
            self.logger.info(f"Extracted likes count: {likes_count}")
            comments_count = self._extract_comments_count(post_element)
            self.logger.info(f"Extracted comments count: {comments_count}")
            shares_count = self._extract_shares_count(post_element)
            self.logger.info(f"Extracted shares count: {shares_count}")

            # Get group name
            group_name = self._extract_group_name()
            self.logger.info(f"Extracted group name: {group_name}")

            return FacebookPost(
                post_id=post_id,
                author=author,
                content=content,
                timestamp=timestamp,
                post_url=post_url,
                url=post_url,
                scraped_at=self._get_current_timestamp(),
                likes_count=likes_count,
                comments_count=comments_count,
                shares_count=shares_count,
                group_name=group_name,
                metadata={"platform": "facebook", "content_type": "post"},
            )

        except Exception as e:
            self.logger.error(f"Error extracting post data: {str(e)}")
            return None

    def _scroll_to_load_posts(self, max_posts: int):
        """Scroll down to load more posts."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return

        posts_found = 0
        # last_height = self.driver.execute_script("return document.body.scrollHeight")

        while posts_found < max_posts:
            # Choose scrolling method based on fast mode
            if self.fast_mode:
                self.human_behavior.fast_scroll("down", random.randint(400, 800))
            else:
                self.human_behavior.human_scroll("down", random.randint(400, 800))

            # Count current posts
            current_posts = len(
                self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='article']"
                )
            )
            posts_found = current_posts
            self.logger.info(f"Current posts found: {posts_found}")

            # Check if we've reached the bottom
            # new_height = self.driver.execute_script("return document.body.scrollHeight")
            # if new_height == last_height:
            #     break
            # last_height = new_height

            # Occasionally scroll back up a bit (like human behavior)
            if random.random() < 0.15:  # 15% chance
                if self.fast_mode:
                    self.human_behavior.fast_scroll("up", random.randint(100, 300))
                    time.sleep(0.2)  # Reduced delay for fast mode
                else:
                    self.human_behavior.human_scroll("up", random.randint(100, 300))
                    self.human_behavior.random_delay(1, 2)

            # Safety check to prevent infinite scrolling
            if posts_found > max_posts * 2:
                break

    def _extract_posts(self, max_posts: int) -> List[FacebookPost]:
        """Extract post information from the page."""
        if not self.driver:
            self.logger.error("WebDriver not initialized")
            return []

        posts = []

        # Find post containers
        self.logger.debug("Locating post containers with selector: [data-testid='post_message']")
        post_containers = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='article']"
        )

        self.logger.info(f"Found {len(post_containers)} post containers")

        for i, container in enumerate(post_containers[:max_posts]):
            try:
                post = self.extract_content_data(container)
                if post:
                    posts.append(post)
            except Exception as e:
                self.logger.warning(f"Error extracting post {i}: {str(e)}")
                continue

        return posts

    def _extract_engagement_count(self, container, engagement_type: str) -> int:
        """Extract engagement count (likes, comments, shares)."""
        try:
            # Try different selectors for engagement counts
            selectors = [
                f'[data-testid="{engagement_type}_count"]',
                f'[aria-label*="{engagement_type}"]',
                f'span[class*="{engagement_type}"]',
            ]

            for selector in selectors:
                try:
                    element = container.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    # Extract number from text like "1.2K likes" or "123"
                    numbers = re.findall(r"[\d,]+", text)
                    if numbers:
                        return int(numbers[0].replace(",", ""))
                except Exception:
                    continue

            return 0

        except Exception:
            return 0

    def _extract_group_name(self) -> str:
        """Extract group name from the page."""
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized")
                return "Unknown Group"

            # Try to find group name in various locations
            selectors = ['h1[data-testid="group_name"]', 'h1[class*="group"]', "title"]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name and name != "Facebook":
                        return name
                except Exception:
                    continue

            # Fallback to URL-based extraction
            url = self.driver.current_url
            if "/groups/" in url:
                parts = url.split("/groups/")
                if len(parts) > 1:
                    group_part = parts[1].split("/")[0]
                    return group_part.replace("-", " ").title()

            return "Unknown Group"

        except Exception:
            return "Unknown Group"

    def _extract_post_id(self, post_element) -> Optional[str]:
        """Extract post ID from post element."""
        try:
            # Try to find post ID from various sources
            selectors = [
                '[data-testid="post_id"]',
                'a[href*="/permalink/"]',
                '[data-ft*="post_id"]',
            ]

            for selector in selectors:
                try:
                    element = post_element.find_element(By.CSS_SELECTOR, selector)
                    if selector == 'a[href*="/permalink/"]':
                        href = element.get_attribute("href")
                        if href and "/permalink/" in href:
                            return href.split("/permalink/")[-1].split("/")[0]
                    else:
                        post_id = element.get_attribute("data-ft") or element.text
                        if post_id:
                            return post_id
                except Exception:
                    continue

            # Fallback: generate ID from timestamp and content hash
            return f"post_{int(time.time())}_{hash(str(post_element)) % 10000}"

        except Exception:
            return None

    def _extract_author(self, post_element) -> Optional[str]:
        """Extract author name from post element."""
        try:
            # Try different selectors for author
            selectors = [
                "h3 a",
                '[data-testid="post_author_link"]',
                '[class*="author"] a',
                'a[role="link"]',
            ]

            for selector in selectors:
                try:
                    element = post_element.find_element(By.CSS_SELECTOR, selector)
                    author = element.text.strip()
                    if author and author != "Facebook":
                        return author
                except Exception:
                    continue

            return None

        except Exception:
            return None

    def _extract_post_content(self, post_element) -> Optional[str]:
        """Extract post content from post element."""
        try:
            # Try different selectors for post content
            selectors = [
                '[data-testid="post_message"]',
                '[class*="post_content"]',
                '[class*="message"]',
                'div[dir="auto"]',
            ]

            for selector in selectors:
                try:
                    element = post_element.find_element(By.CSS_SELECTOR, selector)
                    content = element.text.strip()
                    if content:
                        return content
                except Exception:
                    continue

            return None

        except Exception:
            return None

    def _extract_timestamp(self, post_element) -> str:
        """Extract timestamp from post element."""
        try:
            # Try different selectors for timestamp
            selectors = [
                'a[href*="/permalink/"]',
                '[class*="timestamp"]',
                '[class*="time"]',
                "abbr",
            ]

            for selector in selectors:
                try:
                    element = post_element.find_element(By.CSS_SELECTOR, selector)
                    timestamp = element.get_attribute("title") or element.text
                    if timestamp:
                        return timestamp
                except Exception:
                    continue

            return "Unknown"

        except Exception:
            return "Unknown"

    def _extract_post_url(self, post_element) -> str:
        """Extract post URL from post element."""
        try:
            # Try to find post URL
            selectors = [
                'a[href*="/permalink/"]',
                'a[href*="/posts/"]',
                'a[href*="/story/"]',
            ]

            for selector in selectors:
                try:
                    element = post_element.find_element(By.CSS_SELECTOR, selector)
                    href = element.get_attribute("href")
                    if href:
                        return href
                except Exception:
                    continue

            # Fallback to current page URL
            return self.driver.current_url if self.driver else ""

        except Exception:
            return self.driver.current_url if self.driver else ""

    def _extract_likes_count(self, post_element) -> int:
        """Extract likes count from post element."""
        return self._extract_engagement_count(post_element, "like")

    def _extract_comments_count(self, post_element) -> int:
        """Extract comments count from post element."""
        return self._extract_engagement_count(post_element, "comment")

    def _extract_shares_count(self, post_element) -> int:
        """Extract shares count from post element."""
        return self._extract_engagement_count(post_element, "share")

    def save_posts_to_database(self, posts: List[FacebookPost]) -> int:
        """Save scraped posts to the database using DatabaseManager."""
        if not posts:
            return 0

        # Convert FacebookPost objects to dictionaries
        posts_data = [post.to_dict() for post in posts]
        return self.db_manager.save_posts(posts_data)

    def save_posts_to_json(
        self, posts: List[FacebookPost], filename: str = "facebook_posts.json"
    ) -> bool:
        """Save scraped posts to a JSON file."""
        try:
            posts_data = [post.to_dict() for post in posts]

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(posts_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(posts)} posts to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving posts to JSON: {str(e)}")
            return False

    def monitor_group(
        self, group_url: str, interval_minutes: int = 30, max_posts: int = 20
    ):
        """Continuously monitor a Facebook group for new posts."""
        self.logger.info(f"Starting monitoring of group: {group_url}")
        self.logger.info(f"Check interval: {interval_minutes} minutes")
        self.logger.info(f"Max posts per check: {max_posts}")

        def check_for_new_posts():
            try:
                posts = self.scrape_content(group_url, max_posts)
                if posts:
                    saved_count = self.save_posts_to_database(posts)
                    self.save_posts_to_json(posts)
                    self.logger.info(
                        f"Check completed: {len(posts)} posts found, {saved_count} saved"
                    )
                else:
                    self.logger.info("Check completed: No new posts found")
            except Exception as e:
                self.logger.error(f"Error during monitoring check: {str(e)}")

        # Schedule the monitoring
        schedule.every(interval_minutes).minutes.do(check_for_new_posts)

        # Run initial check
        check_for_new_posts()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        finally:
            self.close()

    def post_scraping_cleanup(self) -> bool:
        """Perform cleanup after scraping."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None

            # Terminate any remaining Chrome processes
            self.chrome_manager.terminate_selenium_chrome_sessions()

            return True
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            return False

    def close(self):
        """Close the WebDriver and clean up resources."""
        # Log human behavior statistics before closing
        if hasattr(self, "human_behavior"):
            human_stats = self.human_behavior.get_session_stats()
            self.logger.info(f"Human behavior session stats: {human_stats}")

        self.post_scraping_cleanup()
        if self.db_manager:
            self.db_manager.close()
        super().close()

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get comprehensive scraping statistics."""
        base_stats = super().get_scraping_stats()
        db_stats = self.db_manager.get_database_stats()

        stats = {
            **base_stats,
            "database_stats": db_stats,
            "driver_active": self.driver is not None,
        }

        # Add human behavior statistics
        if hasattr(self, "human_behavior"):
            stats.update(self.human_behavior.get_session_stats())

        return stats
