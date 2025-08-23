#!/usr/bin/env python3
"""
Facebook UI Screenshot Scraper
Locates Facebook posts using HTML tags and captures screenshots for OCR processing.
No data extraction - only post location and screenshot capture.
"""

import time
import os
import random
from datetime import datetime
from typing import List, Optional, Dict, Any

from selenium.webdriver.common.by import By
from fake_useragent import UserAgent

from .base_scraper import BaseScraper
from database.database import DatabaseManager
from utils.human_behavior import HumanBehavior
from utils.chrome_driver_setup import ChromeDriverSetup


class FacebookUIScraper(BaseScraper):
    """Facebook scraper that locates posts using HTML tags and captures screenshots for OCR processing."""

    def __init__(self, db_path: str = "facebook_posts.db", validate_posts: bool = True):
        super().__init__(name="FacebookUIScraper")
        self.db_manager = DatabaseManager(db_path)
        self.driver = None
        self.screenshot_dir = "facebook_screenshots"
        self.is_authenticated = False
        self.ua = UserAgent()
        self.human_behavior = HumanBehavior()
        self.validate_posts = validate_posts  # Switch to enable/disable post validation

        # Create screenshot directory
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def setup_driver(self, headless: bool = True) -> bool:
        """Setup Chrome WebDriver with human behavior enhancements and profile management."""
        try:
            # Create Chrome driver setup instance
            chrome_setup = ChromeDriverSetup()

            # Check profile status first
            profile_info = chrome_setup.check_profile_status()
            self.logger.info(f"Profile Status: {profile_info['profile_status']}")

            # Define enhancement function for human behavior
            def enhance_options(options):
                self.human_behavior.enhance_chrome_options(options)

            # Setup driver with fallback options and profile management
            self.driver = chrome_setup.setup_driver(
                headless=headless, enhance_options=enhance_options
            )

            # Set driver in human behavior module
            self.human_behavior.set_driver(self.driver)

            # Remove automation flags
            self.human_behavior.remove_automation_flags()

            self.logger.info(
                "Chrome WebDriver setup completed with human behavior enhancements and profile management"
            )
            self.logger.info(
                "🔐 Your Facebook login session will persist between runs!"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup driver: {str(e)}")
            return False

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Facebook using provided credentials or existing profile session."""
        try:
            if not self.driver:
                self.logger.error(
                    "WebDriver not initialized. Call setup_driver() first."
                )
                return False

            # First, check if already logged in from profile
            self.logger.info("🔍 Checking for existing Facebook session...")
            if self._check_if_already_logged_in():
                self.logger.info("✅ Already authenticated with Facebook from profile!")
                self.logger.info(
                    "🔐 Your session is persistent - no need to login again!"
                )
                self.is_authenticated = True
                return True

            # If not logged in, proceed with credentials
            email = credentials.get("email")
            password = credentials.get("password")

            if not email or not password:
                self.logger.error("Email and password are required for authentication")
                return False

            # Navigate to Facebook login page
            self.driver.get("https://www.facebook.com/login")
            self.human_behavior.random_delay(2, 4)

            # Find and fill email field with human-like behavior
            email_field = self.driver.find_element(By.ID, "email")
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
                self.logger.info("✅ Login successful!")
                self.logger.info("💾 Your session has been saved to the profile!")
                self.logger.info(
                    "🔐 Next time you run the scraper, you'll be automatically logged in!"
                )
                self.is_authenticated = True
                return True
            else:
                self.logger.warning("❌ Login failed - still on login page")
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
                '[data-testid="blue_bar_profile_link"]',
                '[aria-label="Your profile"]',
                '[data-testid="pagelet_welcome_box"]',
                '[data-testid="nav_bar_profile"]',
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
                try:
                    login_form = self.driver.find_element(By.ID, "email")
                    if not login_form.is_displayed():
                        self.logger.info(
                            "No login form visible, likely already logged in"
                        )
                        return True
                except Exception:
                    self.logger.info("No login form found, likely already logged in")
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking login status: {str(e)}")
            return False

    def scrape_posts(
        self, target_url: str, max_posts: int = 10
    ) -> List[Dict[str, Any]]:
        """Scrape Facebook posts and capture screenshots with proper content extraction."""
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized")
                return []

            # Navigate to the target URL
            self.logger.info(f"🌐 Navigating to: {target_url}")
            self.driver.get(target_url)
            self.human_behavior.random_delay(3, 5)  # Wait for page to load

            # Check if we need to login
            if not self.is_authenticated:
                self.logger.info("🔐 Authentication required...")
                if not self._check_if_already_logged_in():
                    self.logger.error("❌ Not logged in and no credentials provided")
                    return []
                else:
                    self.logger.info("✅ Already logged in, proceeding...")
                    # Navigate back to target URL after login check
                    self.driver.get(target_url)
                    self.human_behavior.random_delay(3, 5)

            # Start the scroll-find-capture process
            self.logger.info(
                f"🚀 Starting Facebook post scraping for max {max_posts} posts..."
            )

            # Implement scroll -> find -> capture -> repeat logic
            posts = []
            scroll_attempts = 0
            max_scroll_attempts = 10

            while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
                # Find post containers in current view
                post_containers = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='article']"
                )
                self.logger.info(
                    f"📱 Found {len(post_containers)} potential post containers in current view"
                )

                for i, container in enumerate(post_containers):
                    if len(posts) >= max_posts:
                        break

                    try:
                        # Get container info for logging
                        role = container.get_attribute("role") or "no-role"
                        data_testid = (
                            container.get_attribute("data-testid") or "no-testid"
                        )
                        class_attr = container.get_attribute("class") or "no-class"

                        # Apply validation logic based on validate_posts setting
                        if self.validate_posts:
                            # Validation enabled: check if it's an actual post
                            is_valid_post = self._is_actual_post(container)
                            
                            if is_valid_post:
                                # Valid post found - capture screenshot
                                screenshot_path = self._capture_screenshot(container, i + 1)
                                
                                if screenshot_path:
                                    # Create post data for valid posts
                                    post_data = {
                                        "post_id": f"post_{len(posts) + 1:03d}",
                                        "screenshot_path": screenshot_path,
                                        "scraped_at": datetime.now().isoformat(),
                                        "is_valid_post": True,
                                        "container_info": {
                                            "role": role,
                                            "data_testid": data_testid,
                                            "class": class_attr,
                                        },
                                    }
                                    posts.append(post_data)
                                    self.logger.info(
                                        f"✅ Captured VALID post {len(posts)}: {os.path.basename(screenshot_path)}"
                                    )
                                else:
                                    self.logger.warning(
                                        f"Failed to capture screenshot for container {i + 1}"
                                    )
                            else:
                                # Invalid post - skip screenshot
                                self.logger.info(
                                    f"ℹ️ Container {i + 1} is not a valid post (role='{role}', testid='{data_testid}') - skipping screenshot"
                                )
                        else:
                            # Validation disabled: treat all containers as valid posts
                            # Skip _is_actual_post process entirely
                            screenshot_path = self._capture_screenshot(container, i + 1)
                            
                            if screenshot_path:
                                # Create post data for all containers
                                post_data = {
                                    "post_id": f"post_{len(posts) + 1:03d}",
                                    "screenshot_path": screenshot_path,
                                    "scraped_at": datetime.now().isoformat(),
                                    "is_valid_post": True,  # All containers treated as valid
                                    "container_info": {
                                        "role": role,
                                        "data_testid": data_testid,
                                        "class": class_attr,
                                    },
                                }
                                posts.append(post_data)
                                self.logger.info(
                                    f"📸 Captured ALL container {len(posts)}: {os.path.basename(screenshot_path)} (validation disabled)"
                                )
                            else:
                                self.logger.warning(
                                    f"Failed to capture screenshot for container {i + 1}"
                                )

                    except Exception as e:
                        self.logger.warning(
                            f"Error processing container {i + 1}: {str(e)}"
                        )
                        continue

                # Scroll to load more content if we need more posts
                if len(posts) < max_posts:
                    self.human_behavior.human_scroll("down", random.randint(600, 1000))
                    self.human_behavior.random_delay(2, 4)
                    scroll_attempts += 1
                    self.logger.info(
                        f"📜 Scrolling to load more content... (attempt {scroll_attempts})"
                    )
                else:
                    break

            self.logger.info(
                f"🎯 Scraping completed! Captured {len(posts)} posts in {scroll_attempts} scroll attempts"
            )
            return posts

        except Exception as e:
            self.logger.error(f"Error scraping posts: {str(e)}")
            return []

    def _is_actual_post(self, container) -> bool:
        """Determine if a container is an actual post, not a comment or other element."""
        try:
            # Check for post-specific attributes
            role = container.get_attribute("role")
            data_testid = container.get_attribute("data-testid")
            class_attr = container.get_attribute("class") or ""

            # Enhanced post detection for Facebook 2025 UI
            # Check multiple indicators to confirm it's a real post

            # 1. Primary check: role="article" or data-testid containing "post"
            if role != "article" and (
                not data_testid or "post" not in str(data_testid)
            ):
                return False

            # 2. Check for modern Facebook post containers using class patterns
            modern_post_classes = [
                "userContentWrapper",  # Classic Facebook post wrapper
                "du4w35lb",  # Modern Facebook post class
                "k4urcfbm",  # Another modern post identifier
                "l9j0dhe7",  # Post container class
                "sjgh65i0",  # Post wrapper class
            ]

            has_modern_post_class = any(
                cls in class_attr for cls in modern_post_classes
            )

            # 3. Check for post message content (multiple selectors for robustness)
            post_message_selectors = [
                "[data-testid='post_message']",
                "[data-testid='message']",
                "div[data-testid='post_message']",
                "div[data-testid='message']",
            ]

            has_post_message = False
            for selector in post_message_selectors:
                if container.find_elements(By.CSS_SELECTOR, selector):
                    has_post_message = True
                    break

            if not has_post_message:
                return False

            # 4. Check for author information (multiple selectors)
            author_selectors = [
                "h3 a",
                "a[class*='x1i10hfl']",
                "[data-testid='post_author']",
                "[data-testid='author']",
                "[data-testid='user_name']",
                "a[href*='/profile.php']",
                "a[href*='/']",
            ]

            has_author = False
            for selector in author_selectors:
                if container.find_elements(By.CSS_SELECTOR, selector):
                    has_author = True
                    break

            if not has_author:
                return False

            # 5. Check that it's NOT a comment, reply, or other UI element
            non_post_indicators = [
                "[data-testid='comment']",
                "[data-testid='reply']",
                "[data-testid='comment_reply']",
                "div[aria-label*='comment']",
                "div[aria-label*='reply']",
                "[data-testid='UFI2Comment']",
                "[data-testid='UFI2Reply']",
            ]

            for indicator in non_post_indicators:
                if container.find_elements(By.CSS_SELECTOR, indicator):
                    return False

            # 6. Additional validation: Check for engagement elements (likes, comments, shares)
            engagement_selectors = [
                "[data-testid='UFI2ReactionsCount']",
                "[data-testid='UFI2CommentsCount']",
                "[data-testid='UFI2SharesCount']",
                "[aria-label*='reaction']",
                "[aria-label*='comment']",
                "[aria-label*='share']",
            ]

            has_engagement = any(
                container.find_elements(By.CSS_SELECTOR, selector)
                for selector in engagement_selectors
            )

            # 7. Final validation: Must pass all checks
            return has_modern_post_class or has_engagement

        except Exception as e:
            self.logger.debug(f"Error checking if actual post: {str(e)}")
            return False

    def _capture_screenshot(self, container, post_index: int) -> Optional[str]:
        """Capture a screenshot of a post container."""
        try:
            if not self.driver:
                return None

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"post_{post_index:03d}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)

            # Capture screenshot of the container
            container.screenshot(filepath)

            self.logger.info(f"📸 Screenshot captured: {filename}")
            return filepath

        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")
            return None

    def scrape_content(self, target_url: str, max_items: int = 20) -> List[Any]:
        """Implementation of abstract method from BaseScraper."""
        return self.scrape_posts(target_url, max_items)

    def extract_content_data(self, content_element) -> Optional[Any]:
        """Implementation of abstract method from BaseScraper."""
        # This method is not used in screenshot-only mode
        return None
