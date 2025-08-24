#!/usr/bin/env python3
"""
Facebook UI Screenshot Scraper
Locates Facebook posts using HTML tags and captures screenshots for OCR processing.
Also extracts text content and image information from posts.
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
                # Find post containers in current view using Facebook's actual feed structure
                post_containers = []

                try:
                    # First try to find the feed container
                    feed_container = self.driver.find_element(
                        By.CSS_SELECTOR, "div[role='feed']"
                    )

                    # Then find posts within the feed using the specific class combination
                    post_containers = feed_container.find_elements(
                        By.CSS_SELECTOR, "div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z"
                    )

                    if post_containers:
                        self.logger.info("✅ Found posts using Facebook feed structure")
                    else:
                        self.logger.info(
                            "Feed found but no posts with expected classes"
                        )

                except Exception as e:
                    self.logger.debug(f"Feed structure not found: {str(e)}")

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

                        # Wait for the container to be fully loaded before processing
                        if self._wait_for_container_loaded(container):
                            # Look for and click expandable buttons before processing
                            self._click_expandable_buttons(container, i + 1)
                            
                            # Extract content data after clicking expand buttons
                            content_data = self.extract_content_data(container)
                            
                            # Apply validation logic based on validate_posts setting
                            if self.validate_posts:
                                self.logger.info("🧐 Validating posts")
                                # Validation enabled: check if it's an actual post
                                is_valid_post = self._is_actual_post(container)
                                
                                if is_valid_post:
                                    # Valid post found - capture screenshot
                                    screenshot_path = (
                                        self._capture_screenshot_with_wait(
                                            container, i + 1
                                        )
                                    )

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
                                            "content_data": content_data,
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
                                self.logger.info("🧐❌ Validating post disable")
                                # Validation disabled: treat all containers as valid posts
                                # Skip _is_actual_post process entirely
                                screenshot_path = self._capture_screenshot_with_wait(
                                    container, i + 1
                                )

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
                                        "content_data": content_data,
                                    }
                                    posts.append(post_data)
                                    self.logger.info(
                                        f"📸 Captured ALL container {len(posts)}: {os.path.basename(screenshot_path)} (validation disabled)"
                                    )
                                else:
                                    self.logger.warning(
                                        f"Failed to capture screenshot for container {i + 1}"
                                    )
                        else:
                            # Container not fully loaded - skip processing
                            self.logger.warning(
                                f"⚠️ Container {i + 1} not fully loaded - skipping processing"
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
            
            # Automatically save detailed content data to JSON file
            if posts:
                try:
                    # Save detailed content data with analysis
                    detailed_json_path = self.save_content_data_to_detailed_json(posts)
                    if detailed_json_path:
                        self.logger.info(f"💾 Detailed content data saved to: {detailed_json_path}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to save content data to JSON: {str(e)}")
            
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
                "xd9ej83",  # New Facebook feed post class
                "x162z183",  # New Facebook feed post class
                "xsag5q8",  # New Facebook feed post class
                "xf7dkkf",  # New Facebook feed post class
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

    def _wait_for_container_loaded(self, container) -> bool:
        """Wait for a container to be fully loaded before processing."""
        try:
            if not self.driver:
                return False

            # Wait for key elements that indicate the post is fully loaded
            wait_selectors = [
                "[data-testid='post_message']",  # Post content
                "[data-testid='message']",  # Alternative post content
                "h3 a",  # Author name
                "a[class*='x1i10hfl']",  # Author link
                "[data-testid='post_author']",  # Author
                "[data-testid='author']",  # Alternative author
            ]

            # Check if at least one key element is present and visible
            for selector in wait_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        # Found a key element, wait a bit more for content to stabilize
                        self.human_behavior.random_delay(0.5, 1.5)
                        return True
                except Exception:
                    continue
                            
            # If no key elements found, wait a bit and check again
            self.human_behavior.random_delay(1, 2)

            # Final check
            for selector in wait_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return True
                except Exception:
                    continue
                    
            return False

        except Exception as e:
            self.logger.debug(f"Error waiting for container to load: {str(e)}")
            return False

    def _capture_screenshot_with_wait(
        self, container, post_index: int
    ) -> Optional[str]:
        """Capture a screenshot of a post container with additional waiting for content stability."""
        try:
            if not self.driver:
                return None
                
            # Wait a bit more for any remaining animations or content to settle
            self.human_behavior.random_delay(0.5, 1.0)

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

    def _click_expandable_buttons(self, container, post_index: int) -> None:
        """Look for and click expandable buttons (like 'See more', 'Show more') within a post container."""
        try:
            if not self.driver:
                return

            # Common expandable button selectors
            expand_button_selectors = [
                # Facebook's "See more" button with full class list
                "div.x1i10hfl.xjbqb8w.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x972fbf.x10w94by.x1qhh985.x14e42zd.x9f619.x1ypdohk.xt0psk2.x3ct3a4.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.xkrqix3.x1sur9pj.xzsf02u.x1s688f[role='button']",
                # # Partial class match for "See more" button (more flexible)
                # "div[class*='x1i10hfl'][class*='x1ypdohk'][role='button']",
                # # Button containing "See more" text
                # "div[role='button']:has-text('See more')",
            ]

            buttons_clicked = 0
            
            for selector in expand_button_selectors:
                try:
                    # Find buttons within this container
                    buttons = container.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Find the first clickable button instead of looping through all
                    first_clickable_button = None
                    for button in buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                first_clickable_button = button
                                break
                        except Exception as e:
                            self.logger.debug(f"Error checking button in post {post_index}: {str(e)}")
                            continue
                    
                    # Process only the first clickable button found
                    if first_clickable_button:
                        try:
                            # Get button text for logging
                            button_text = first_clickable_button.text or first_clickable_button.get_attribute("aria-label") or "unknown"
                            
                            # Click the first button found
                            self.human_behavior.human_click(first_clickable_button)
                            buttons_clicked += 1
                            
                            self.logger.info(f"🔘 Clicked FIRST expand button '{button_text}' in post {post_index}")
                            
                            # Wait a bit for content to expand
                            self.human_behavior.random_delay(0.5, 1.0)
                            
                        except Exception as e:
                            self.logger.debug(f"Failed to click first button in post {post_index}: {str(e)}")
                            
                except Exception as e:
                    self.logger.debug(f"Error with selector '{selector}' in post {post_index}: {str(e)}")
                    continue
            
            if buttons_clicked > 0:
                self.logger.info(f"🔘 Total buttons clicked in post {post_index}: {buttons_clicked}")
            else:
                self.logger.debug(f"🔘 No expandable buttons found in post {post_index}")
            
        except Exception as e:
            self.logger.debug(f"Error clicking expandable buttons in post {post_index}: {str(e)}")

    def extract_content_data(self, container) -> Optional[Dict[str, Any]]:
        """Extract text content and image information from a post container using specific class names."""
        try:
            if not container:
                return None

            content_data = {
                "post_text": None,
                "images": [],
                "extraction_timestamp": datetime.now().isoformat()
            }

            # Extract post text using the class from post_example.py
            try:
                # Look for post text with the specific class pattern
                post_text_selectors = [
                    "div.xdj266r.x14z9mp.xat24cr.x1lziwak.x1vvkbs.x126k92a",  # From post_example.py
                    "div[data-testid='post_message']",  # Fallback
                    "div[data-testid='message']",  # Alternative fallback
                ]
                
                for selector in post_text_selectors:
                    text_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    if text_elements:
                        for text_elem in text_elements:
                            if text_elem.is_displayed():
                                text_content = text_elem.text.strip()
                                if text_content:
                                    content_data["post_text"] = text_content
                                    self.logger.debug(f"📝 Extracted post text: {text_content[:100]}...")
                                    break
                        if content_data["post_text"]:
                            break
            except Exception as e:
                self.logger.debug(f"Error extracting post text: {str(e)}")

            # Extract image information using the classes from post_example.py
            try:
                # Look for image containers with the specific class pattern
                image_container_selectors = [
                    "div.x1i10hfl.xjbqb8w.x1ejq31n.x13faqbe.x1vvkbs.x126k92a.x193iq5w",  # From post_example.py
                    "div.x17z8epw.x579bpy.x1s688f.x2b8uid",  # Image remaining class
                    "img[src*='scontent']",  # Facebook image URLs
                    "img[data-visualcompletion='media-vc-image']",  # Facebook image attribute
                ]
                
                for selector in image_container_selectors:
                    image_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    
                    for img_elem in image_elements:
                        try:
                            if img_elem.is_displayed():
                                # Extract image information
                                img_src = img_elem.get_attribute("src")
                                img_alt = img_elem.get_attribute("alt") or "No alt text"
                                img_title = img_elem.get_attribute("title") or "No title"
                                
                                if img_src and "scontent" in img_src:  # Facebook CDN URL
                                    image_info = {
                                        "src": img_src,
                                        "alt": img_alt,
                                        "title": img_title,
                                        "class": img_elem.get_attribute("class") or "unknown"
                                    }
                                    content_data["images"].append(image_info)
                                    self.logger.debug(f"🖼️ Found image: {img_alt[:50]}...")
                        except Exception as e:
                            self.logger.debug(f"Error processing image element: {str(e)}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Error extracting image information: {str(e)}")

            # Extract image links if available
            try:
                # Look for clickable image links
                image_link_selectors = [
                    "a[class*='x1i10hfl'][class*='x1qjc9v5'][role='link']",  # From post_example.py (partial)
                    "a[href*='photo']",  # Facebook photo links
                    "a[href*='story_fbid']",  # Facebook story links
                ]
                
                for selector in image_link_selectors:
                    link_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    
                    for link_elem in link_elements:
                        try:
                            if link_elem.is_displayed():
                                href = link_elem.get_attribute("href")
                                if href and ("photo" in href or "story_fbid" in href):
                                    # Check if this link corresponds to an image we already found
                                    link_text = link_elem.text.strip()
                                    link_aria_label = link_elem.get_attribute("aria-label") or ""
                                    
                                    link_info = {
                                        "href": href,
                                        "text": link_text,
                                        "aria_label": link_aria_label,
                                        "class": link_elem.get_attribute("class") or "unknown"
                                    }
                                    
                                    # Add to images if it's not already there
                                    if not any(img.get("href") == href for img in content_data["images"]):
                                        content_data["images"].append(link_info)
                                        self.logger.debug(f"🔗 Found image link: {href[:100]}...")
                        except Exception as e:
                            self.logger.debug(f"Error processing image link: {str(e)}")
                            continue
                            
            except Exception as e:
                self.logger.debug(f"Error extracting image links: {str(e)}")

            # Log extraction summary
            if content_data["post_text"] or content_data["images"]:
                self.logger.info(f"📊 Content extracted: {len(content_data['images'])} images, text: {'Yes' if content_data['post_text'] else 'No'}")
                return content_data
            else:
                self.logger.debug("No content extracted from container")
                return None

        except Exception as e:
            self.logger.error(f"Error in extract_content_data: {str(e)}")
            return None

    def save_content_data_to_detailed_json(self, posts: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Save detailed content data to a JSON file with enhanced formatting and analysis."""
        try:
            if not posts:
                self.logger.warning("No posts data to save")
                return ""

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"facebook_detailed_content_{timestamp}.json"

            # Prepare detailed data structure
            detailed_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_posts": len(posts),
                    "scraper_version": "1.0",
                    "facebook_ui_version": "2025",
                    "extraction_method": "class_based_selectors",
                    "content_summary": {
                        "posts_with_text": 0,
                        "posts_with_images": 0,
                        "total_images_found": 0,
                        "posts_with_both": 0
                    }
                },
                "posts": []
            }

            # Process each post with detailed analysis
            for post in posts:
                content_data = post.get("content_data", {})
                
                # Count content types
                has_text = bool(content_data.get("post_text"))
                has_images = len(content_data.get("images", [])) > 0
                
                if has_text:
                    detailed_data["metadata"]["content_summary"]["posts_with_text"] += 1
                if has_images:
                    detailed_data["metadata"]["content_summary"]["posts_with_images"] += 1
                if has_text and has_images:
                    detailed_data["metadata"]["content_summary"]["posts_with_both"] += 1
                
                detailed_data["metadata"]["content_summary"]["total_images_found"] += len(content_data.get("images", []))

                # Create detailed post entry
                detailed_post = {
                    "post_id": post.get("post_id", "unknown"),
                    "scraped_at": post.get("scraped_at", ""),
                    "screenshot_path": post.get("screenshot_path", ""),
                    "is_valid_post": post.get("is_valid_post", False),
                    "container_info": post.get("container_info", {}),
                    "content_analysis": {
                        "has_text": has_text,
                        "has_images": has_images,
                        "text_length": len(content_data.get("post_text", "")) if content_data.get("post_text") else 0,
                        "image_count": len(content_data.get("images", [])),
                        "content_type": self._determine_content_type(content_data)
                    },
                    "content_data": content_data
                }
                
                detailed_data["posts"].append(detailed_post)

            # Save to JSON file
            filepath = os.path.join(os.getcwd(), str(filename))
            
            import json
            with open(filepath, 'w', encoding='utf-8') as json_file:
                json.dump(detailed_data, json_file, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"💾 Detailed content data saved to JSON: {filename}")
            self.logger.info(f"📊 Exported {len(posts)} posts with detailed analysis")
            
            return filepath

        except Exception as e:
            self.logger.error(f"Error saving detailed content data to JSON: {str(e)}")
            return ""

    def _determine_content_type(self, content_data: Dict[str, Any]) -> str:
        """Determine the type of content in a post."""
        try:
            has_text = bool(content_data.get("post_text"))
            has_images = len(content_data.get("images", [])) > 0
            
            if has_text and has_images:
                return "text_and_images"
            elif has_text:
                return "text_only"
            elif has_images:
                return "images_only"
            else:
                return "no_content"
        except Exception:
            return "unknown"

    def scrape_content(self, target_url: str, max_items: int = 20) -> List[Any]:
        """Implementation of abstract method from BaseScraper."""
        return self.scrape_posts(target_url, max_items)
