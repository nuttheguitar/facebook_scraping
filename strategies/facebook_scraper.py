#!/usr/bin/env python3
"""
Simple Facebook UI Screenshot Scraper
Captures screenshots of Facebook posts with content expansion for OCR.
"""

import time
import os
import random
from datetime import datetime
from typing import List, Optional, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

from .base_scraper import BaseScraper
from database.database import DatabaseManager
from database.models import FacebookPost
from utils.human_behavior import HumanBehavior
from utils.chrome_driver_setup import ChromeDriverSetup


class FacebookUIScraper(BaseScraper):
    """Simple Facebook scraper that captures post screenshots."""

    def __init__(self, db_path: str = "facebook_posts.db"):
        super().__init__(name="FacebookUIScraper")
        self.db_manager = DatabaseManager(db_path)
        self.driver = None
        self.screenshot_dir = "facebook_screenshots"
        self.is_authenticated = False
        self.ua = UserAgent()
        self.human_behavior = HumanBehavior()
        
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
            self.driver = chrome_setup.setup_driver(headless=headless, enhance_options=enhance_options)
            
            # Set driver in human behavior module
            self.human_behavior.set_driver(self.driver)
            
            # Remove automation flags
            self.human_behavior.remove_automation_flags()
            
            self.logger.info("Chrome WebDriver setup completed with human behavior enhancements and profile management")
            self.logger.info("🔐 Your Facebook login session will persist between runs!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup driver: {str(e)}")
            return False

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Facebook using provided credentials or existing profile session."""
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized. Call setup_driver() first.")
                return False

            # First, check if already logged in from profile
            self.logger.info("🔍 Checking for existing Facebook session...")
            if self._check_if_already_logged_in():
                self.logger.info("✅ Already authenticated with Facebook from profile!")
                self.logger.info("🔐 Your session is persistent - no need to login again!")
                self.is_authenticated = True
                return True

            # If not logged in, proceed with credentials
            email = credentials.get("email")
            password = credentials.get("password")

            if not email or not password:
                self.logger.error("Email and password are required for authentication")
                return False

            self.logger.info("🔑 No existing session found, attempting to login to Facebook...")
            self.logger.info("💾 Your login will be saved to the profile for future use!")

            # Navigate to Facebook login page with human-like behavior
            self.human_behavior.natural_page_navigation("https://www.facebook.com/login")

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
                self.logger.info("✅ Login successful!")
                self.logger.info("💾 Your session has been saved to the profile!")
                self.logger.info("🔐 Next time you run the scraper, you'll be automatically logged in!")
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
            if ("login" not in self.driver.current_url and "facebook.com" in self.driver.current_url):
                try:
                    login_form = self.driver.find_element(By.ID, "email")
                    if not login_form.is_displayed():
                        self.logger.info("No login form visible, likely already logged in")
                        return True
                except Exception:
                    self.logger.info("No login form found, likely already logged in")
                    return True

            return False

        except Exception as e:
            self.logger.warning(f"Error checking login status: {str(e)}")
            return False

    def scrape_posts(self, target_url: str, max_posts: int = 10) -> List[Dict[str, Any]]:
        """Scrape Facebook posts and capture screenshots."""
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized")
                return []

            self.logger.info(f"Scraping posts from: {target_url}")
            
            # Navigate to target page
            self.driver.get(target_url)
            time.sleep(3)
            
            # Scroll to load posts
            self._scroll_to_load_posts(max_posts)
            
            # Find and process posts
            posts = self._find_and_capture_posts(max_posts)
            
            self.logger.info(f"Successfully captured {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error scraping posts: {str(e)}")
            return []

    def _scroll_to_load_posts(self, max_posts: int):
        """Human-like scrolling to load more posts."""
        if not self.driver:
            return
            
        posts_found = 0
        scroll_attempts = 0
        
        while posts_found < max_posts and scroll_attempts < 10:
            # Use human-like scrolling
            scroll_distance = random.randint(600, 1000)
            self.human_behavior.human_scroll("down", scroll_distance)
            self.human_behavior.random_delay(1, 3)
            
            # Count posts
            posts_found = len(self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']"))
            self.logger.info(f"Posts found: {posts_found}")
            
            scroll_attempts += 1
            
            # Occasionally scroll back up a bit (like human behavior)
            if random.random() < 0.15:  # 15% chance
                self.human_behavior.human_scroll("up", random.randint(100, 300))
                self.human_behavior.random_delay(0.5, 1.5)

    def _find_and_capture_posts(self, max_posts: int) -> List[Dict[str, Any]]:
        """Find posts and capture screenshots."""
        if not self.driver:
            return []
            
        posts = []
        
        # Find post containers - be more specific to avoid chat elements and comments
        containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
        
        # Filter out containers that are likely not posts (e.g., chat messages, comments)
        filtered_containers = []
        for i, container in enumerate(containers):
            try:
                # Check if this container has post-like characteristics
                has_post_message = container.find_elements(By.CSS_SELECTOR, "[data-testid='post_message']")
                has_author = container.find_elements(By.CSS_SELECTOR, "h3 a, a[class*='x1i10hfl'], [data-testid='post_author']")
                
                # Additional check: make sure it's not a comment or reply
                is_comment = container.find_elements(By.CSS_SELECTOR, "[data-testid='comment']")
                is_reply = container.find_elements(By.CSS_SELECTOR, "[data-testid='reply']")
                has_comment_indicator = container.find_elements(By.CSS_SELECTOR, "div[aria-label*='comment'], div[aria-label*='reply']")
                
                # Log what we found for debugging
                self.logger.debug(f"Container {i}: has_post_message={len(has_post_message)}, has_author={len(has_author)}, is_comment={len(is_comment)}, is_reply={len(is_reply)}, has_comment_indicator={len(has_comment_indicator)}")
                
                # More lenient filtering: include if it has post message OR author, AND is not clearly a comment/reply
                if ((has_post_message or has_author) and
                        not is_comment and not is_reply and not has_comment_indicator):
                    filtered_containers.append(container)
                    self.logger.debug(f"Container {i} accepted as post-like")
                else:
                    # If still no containers, try even more lenient filtering
                    if len(filtered_containers) == 0:
                        # Check if it has any substantial text content
                        text_elements = container.find_elements(By.CSS_SELECTOR, "div[dir='auto'], span[dir='auto']")
                        has_substantial_text = any(len(elem.text.strip()) > 20 for elem in text_elements if elem.text.strip())
                        
                        if has_substantial_text and not is_comment and not is_reply:
                            filtered_containers.append(container)
                            self.logger.debug(f"Container {i} accepted with lenient filtering (substantial text)")
                        else:
                            self.logger.debug(f"Container {i} rejected - missing post characteristics or is comment/reply")
                    else:
                        self.logger.debug(f"Container {i} rejected - missing post characteristics or is comment/reply")
            except Exception as e:
                self.logger.debug(f"Error processing container {i}: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(containers)} total containers, filtered to {len(filtered_containers)} post-like containers")
        
        # If no containers were found, let's debug what's actually there
        if len(filtered_containers) == 0 and len(containers) > 0:
            self.logger.warning("No containers passed filtering. Debugging container contents...")
            for i, container in enumerate(containers[:2]):  # Debug first 2 containers
                try:
                    self._debug_container_structure(container, i)
                except Exception as e:
                    self.logger.error(f"Error debugging container {i}: {str(e)}")
        
        containers = filtered_containers
        
        for i, container in enumerate(containers[:max_posts]):
            try:
                post_data = self._process_post(container, i + 1)
                if post_data:
                    posts.append(post_data)
            except Exception as e:
                self.logger.warning(f"Error processing post {i+1}: {str(e)}")
                continue
        
        return posts

    def _process_post(self, container, post_index: int) -> Optional[Dict[str, Any]]:
        """Process a single post: expand content and capture screenshot."""
        try:
            # Expand content
            self._expand_content(container)
            time.sleep(1)
            
            # Capture screenshot
            screenshot_path = self._capture_screenshot(container, post_index)
            if not screenshot_path:
                return None
            
            # Extract basic data
            post_data = {
                "post_id": f"post_{post_index}_{int(time.time())}",
                "author": self._extract_text(container, "h3 a, a[class*='x1i10hfl'], [data-testid='post_author']"),
                "content": self._get_main_post_content(container),  # Use method that gets main post content only
                "timestamp": self._extract_text(container, "abbr, a[href*='/permalink/'], [data-testid='post_timestamp']"),
                "screenshot_path": screenshot_path,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Log what was extracted for debugging
            self.logger.info(f"Post {post_index} - Author: '{post_data['author'][:50]}...' | Content: '{post_data['content'][:100]}...'")
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Error processing post {post_index}: {str(e)}")
            return None

    def _expand_content(self, container):
        """Expand collapsed content by clicking 'Read More' buttons with human behavior."""
        try:
            # Find and click "See more" buttons specifically for post content
            # Use more specific selectors to avoid chat elements
            expand_selectors = [
                "div[role='button']:contains('See more')",
                "[data-testid='post_message'] div[role='button']",
                "div[dir='auto'] div[role='button']",
                "span:contains('See more')",
                "div:contains('See more')"
            ]
            
            clicks = 0
            max_clicks = 3
            
            for selector in expand_selectors:
                if clicks >= max_clicks:
                    break
                    
                try:
                    # Try to find buttons with the specific selector
                    if ":contains" in selector:
                        # Handle :contains pseudo-selector manually
                        text_to_find = selector.split("'")[1]
                        buttons = container.find_elements(By.XPATH, f".//*[contains(text(), '{text_to_find}')]")
                    else:
                        buttons = container.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in buttons:
                        if clicks >= max_clicks:
                            break
                            
                        try:
                            text = button.text.strip()
                            if any(keyword in text for keyword in ["See more", "Read more", "Show more"]):
                                if button.is_displayed() and button.is_enabled():
                                    # Scroll button into view with human behavior
                                    if self.driver:
                                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                    self.human_behavior.random_delay(0.3, 0.8)
                                    
                                    # Click with human behavior
                                    self.human_behavior.human_click(button)
                                    clicks += 1
                                    
                                    # Wait for content to expand
                                    self.human_behavior.random_delay(0.8, 1.5)
                                    self.logger.debug(f"Clicked expand button {clicks}/{max_clicks}")
                                    
                                    # Break inner loop after successful click
                                    break
                        except Exception:
                            continue
                            
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error expanding content: {str(e)}")

    def _capture_screenshot(self, container, post_index: int) -> Optional[str]:
        """Capture screenshot of the post."""
        if not self.driver:
            return None
            
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"post_{post_index:03d}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Scroll post into view with human behavior
            if self.driver:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container)
            self.human_behavior.random_delay(0.8, 1.5)
            
            # Take screenshot
            self.driver.save_screenshot(filepath)
            
            # Try to crop to just the post (optional)
            try:
                from PIL import Image
                
                # Get post position
                location = container.location
                size = container.size
                
                # Validate coordinates
                if location and size and size['width'] > 0 and size['height'] > 0:
                    # Open and crop image
                    img = Image.open(filepath)
                    left = max(0, int(location['x']))
                    top = max(0, int(location['y']))
                    right = min(img.width, int(location['x'] + size['width']))
                    bottom = min(img.height, int(location['y'] + size['height']))
                    
                    if left < right and top < bottom:
                        cropped = img.crop((left, top, right, bottom))
                        cropped.save(filepath)
                        self.logger.info(f"Captured cropped screenshot: {filepath}")
                    else:
                        self.logger.info(f"Captured full screenshot: {filepath}")
                else:
                    self.logger.info(f"Captured full screenshot: {filepath}")
                    
            except ImportError:
                self.logger.info(f"Captured full screenshot (PIL not available): {filepath}")
            except Exception as e:
                self.logger.warning(f"Error cropping, using full screenshot: {str(e)}")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")
            return None

    def _extract_text(self, container, selector: str) -> str:
        """Extract text from container using selector."""
        try:
            elements = container.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                text = element.text.strip()
                if text and len(text) > 1:
                    return text[:500]  # Increased limit for post content
            return ""
        except Exception:
            return ""

    def _extract_post_content(self, container) -> str:
        """Extract post content specifically, filtering out chat and other non-post elements."""
        try:
            # First, try to find the main post message container
            post_message_container = container.find_element(By.CSS_SELECTOR, "[data-testid='post_message']")
            if not post_message_container:
                return ""
            
            # Look for the actual text content within the post message container
            # Facebook stores post content in specific nested elements
            text_selectors = [
                # Most specific: the actual text content
                "div[data-lexical-editor='true']",
                # Fallback: direct text containers
                "div[dir='auto']",
                # Alternative: spans with text
                "span[dir='auto']",
                # Last resort: any text element
                "div"
            ]
            
            for selector in text_selectors:
                try:
                    elements = post_message_container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Filter out very short text
                            # Skip if this looks like metadata or UI elements
                            if not self._is_ui_element(text):
                                # Additional validation: check if this looks like actual post content
                                if self._is_valid_post_content(text):
                                    self.logger.debug(f"Found post content with selector '{selector}': {text[:100]}...")
                                    return text[:1000]  # Allow longer content for posts
                except Exception:
                    continue
            
            return ""
        except Exception as e:
            self.logger.debug(f"Error extracting post content: {str(e)}")
            return ""

    def _debug_container_structure(self, container, container_index: int):
        """Debug the structure of a container to understand why it's not being recognized as a post."""
        try:
            self.logger.info(f"=== Debugging Container {container_index} ===")
            
            # Check for common post elements
            post_message = container.find_elements(By.CSS_SELECTOR, "[data-testid='post_message']")
            author_elements = container.find_elements(By.CSS_SELECTOR, "h3 a, a[class*='x1i10hfl'], [data-testid='post_author']")
            comment_elements = container.find_elements(By.CSS_SELECTOR, "[data-testid='comment']")
            reply_elements = container.find_elements(By.CSS_SELECTOR, "[data-testid='reply']")
            
            self.logger.info(f"Container {container_index} elements found:")
            self.logger.info(f"  - post_message: {len(post_message)}")
            self.logger.info(f"  - author_elements: {len(author_elements)}")
            self.logger.info(f"  - comment_elements: {len(comment_elements)}")
            self.logger.info(f"  - reply_elements: {len(reply_elements)}")
            
            # Check for any text content
            all_text_elements = container.find_elements(By.CSS_SELECTOR, "div[dir='auto'], span[dir='auto']")
            self.logger.info(f"  - text_elements: {len(all_text_elements)}")
            
            # Show some sample text content
            for i, text_elem in enumerate(all_text_elements[:3]):
                text = text_elem.text.strip()
                if text:
                    self.logger.info(f"    Text element {i}: '{text[:100]}...'")
            
            # Check for role and other attributes
            role = container.get_attribute("role")
            aria_label = container.get_attribute("aria-label")
            data_testid = container.get_attribute("data-testid")
            
            self.logger.info(f"  - role: {role}")
            self.logger.info(f"  - aria-label: {aria_label}")
            self.logger.info(f"  - data-testid: {data_testid}")
            
            self.logger.info(f"=== End Container {container_index} Debug ===")
            
        except Exception as e:
            self.logger.error(f"Error debugging container {container_index}: {str(e)}")

    def _get_main_post_content(self, container) -> str:
        """Get the main post content by finding the highest-level text container."""
        try:
            # Find the post message container
            post_message = container.find_element(By.CSS_SELECTOR, "[data-testid='post_message']")
            if not post_message:
                return ""
            
            # Get all direct text children of the post message
            # This should give us the main post content without comments
            direct_text_elements = post_message.find_elements(By.XPATH, "./div[contains(@dir, 'auto')]")
            
            if direct_text_elements:
                # Take the first direct text element (usually the main post)
                main_content = direct_text_elements[0].text.strip()
                if main_content and len(main_content) > 10:
                    return main_content[:1000]
            
            # Fallback: look for the most prominent text element
            all_text_elements = post_message.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
            if all_text_elements:
                # Find the element with the most text (likely the main post)
                longest_text = ""
                for element in all_text_elements:
                    text = element.text.strip()
                    if text and len(text) > len(longest_text) and not self._is_ui_element(text):
                        longest_text = text
                
                if longest_text and self._is_valid_post_content(longest_text):
                    return longest_text[:1000]
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error getting main post content: {str(e)}")
            return ""

    def _is_ui_element(self, text: str) -> bool:
        """Check if text looks like a UI element rather than post content."""
        if not text:
            return True
            
        text_lower = text.lower()
        
        # UI element indicators
        ui_indicators = [
            "like", "comment", "share", "send", "more", "options",
            "report", "hide", "delete", "edit", "save", "bookmark",
            "follow", "unfollow", "block", "mute", "ignore",
            "typing", "online", "last seen", "active now", "is typing",
            "replied to", "replied", "commented", "liked", "shared",
            "sent a message", "message", "chat", "dm", "direct message",
            "reacted to", "reacted", "sent", "received",
            "view all", "see all", "show more", "read more",
            "add friend", "accept", "decline", "pending",
            "public", "friends", "only me", "custom"
        ]
        
        # Check for UI patterns
        if any(indicator in text_lower for indicator in ui_indicators):
            return True
            
        # Check for very short text that's likely UI
        if len(text) < 5:
            return True
            
        # Check for text that's all caps (likely UI buttons)
        if text.isupper() and len(text) < 20:
            return True
            
        return False

    def _is_valid_post_content(self, text: str) -> bool:
        """Validate if the extracted text looks like actual post content."""
        if not text or len(text) < 10:
            return False
            
        # Check for common post content patterns
        post_indicators = [
            "posted", "shared", "wrote", "said", "announced", "published",
            "released", "introduced", "launched", "created", "developed"
        ]
        
        # Check for chat-like patterns that indicate this is not a post
        chat_indicators = [
            "replied to", "replied", "commented", "liked", "shared",
            "sent a message", "message", "chat", "dm", "direct message",
            "typing", "online", "last seen", "active now", "is typing",
            "reacted to", "reacted", "sent", "received"
        ]
        
        text_lower = text.lower()
        
        # If it contains chat indicators, it's likely not a post
        if any(indicator in text_lower for indicator in chat_indicators):
            return False
            
        # If it contains post indicators, it's more likely to be a post
        if any(indicator in text_lower for indicator in post_indicators):
            return True
            
        # Default: if it's substantial text without chat indicators, consider it a post
        return len(text) > 20

    def save_posts_to_database(self, posts: List[Dict[str, Any]]) -> int:
        """Save posts to database."""
        if not posts:
            return 0
            
        try:
            # Convert to FacebookPost objects
            facebook_posts = []
            for post_data in posts:
                post = FacebookPost(
                    post_id=post_data.get("post_id", ""),
                    author=post_data.get("author", ""),
                    content=post_data.get("content", ""),
                    timestamp=post_data.get("timestamp", ""),
                    post_url="",
                    url="",
                    scraped_at=post_data.get("scraped_at", ""),
                    likes_count=0,
                    comments_count=0,
                    shares_count=0,
                    group_name="",
                    metadata=post_data
                )
                facebook_posts.append(post)
            
            # Save to database
            posts_data = [post.to_dict() for post in facebook_posts]
            return self.db_manager.save_posts(posts_data)
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {str(e)}")
            return 0

    def save_posts_to_json(self, posts: List[Dict[str, Any]], filename: str = "facebook_screenshots.json") -> bool:
        """Save posts to JSON file."""
        try:
            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(posts)} posts to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")
            return False

    def get_screenshot_summary(self) -> Dict[str, Any]:
        """Get summary of captured screenshots."""
        try:
            if not os.path.exists(self.screenshot_dir):
                return {"screenshots_found": 0}
            
            files = [f for f in os.listdir(self.screenshot_dir) if f.endswith('.png')]
            total_size = sum(os.path.getsize(os.path.join(self.screenshot_dir, f)) for f in files) / (1024 * 1024)
            
            return {
                "screenshots_found": len(files),
                "screenshot_dir": self.screenshot_dir,
                "total_size_mb": round(total_size, 2)
            }
        except Exception as e:
            return {"error": str(e)}

    def extract_content_data(self, content_element) -> Optional[Dict[str, Any]]:
        """Extract data from content element - implements abstract method."""
        try:
            text = self._extract_text(content_element, "div[dir='auto']")
            return {"content": text} if text else None
        except Exception:
            return None

    def scrape_content(self, target_url: str, max_items: int = 20) -> List[Dict[str, Any]]:
        """Scrape content - implements abstract method."""
        return self.scrape_posts(target_url, max_items)

    def close(self):
        """Close the scraper and clean up."""
        try:
            # Log human behavior statistics before closing
            if hasattr(self, "human_behavior"):
                human_stats = self.human_behavior.get_session_stats()
                self.logger.info(f"Human behavior session stats: {human_stats}")
            
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            self.logger.error(f"Error closing driver: {str(e)}")
        
        if self.db_manager:
            self.db_manager.close()
        
        super().close()

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        base_stats = super().get_scraping_stats()
        screenshot_stats = self.get_screenshot_summary()
        
        stats = {
            **base_stats,
            "driver_active": self.driver is not None,
            "screenshot_stats": screenshot_stats,
            "scraping_strategy": "enhanced_ui_screenshot",
            "authentication_status": self.is_authenticated,
            "human_behavior_enabled": True
        }
        
        # Add human behavior statistics
        if hasattr(self, "human_behavior"):
            stats.update(self.human_behavior.get_session_stats())
        
        return stats
