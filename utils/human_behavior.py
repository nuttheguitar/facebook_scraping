#!/usr/bin/env python3
"""
Human Behavior Module
Provides human-like behaviors for web scrapers to avoid bot detection.
"""

import time
import random
from typing import Dict, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent


class HumanBehavior:
    """Human-like behavior simulation for web scrapers."""

    def __init__(self, driver: Optional[webdriver.Chrome] = None):
        self.driver = driver
        self.ua = UserAgent()
        self.session_start_time = datetime.now()
        self.actions_performed = 0

        # Human-like behavior configuration
        self.config: Dict[str, Any] = {
            "min_delay": 0.5,  # Minimum delay between actions (reduced from 1.0)
            "max_delay": 2.0,  # Maximum delay between actions (reduced from 4.0)
            "scroll_pause_min": 0.1,  # Minimum pause during scrolling (reduced from 0.5)
            "scroll_pause_max": 0.5,  # Maximum pause during scrolling (reduced from 2.0)
            "mouse_movement": True,  # Enable mouse movement simulation
            "random_typing": True,  # Enable random typing delays
            "session_rotation": True,  # Enable session rotation
            "proxy_rotation": False,  # Enable proxy rotation (if configured)
            "fingerprint_randomization": True,  # Enable browser fingerprint randomization
        }

        # User agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        ]

        # Window sizes for fingerprint randomization
        self.window_sizes = [
            (1366, 768),
            (1920, 1080),
            (1440, 900),
            (1536, 864),
            (1600, 900),
            (1280, 720),
            (1024, 768),
            (1280, 1024),
            (1600, 1200),
        ]

    def set_driver(self, driver: webdriver.Chrome):
        """Set the WebDriver instance."""
        self.driver = driver

    def random_delay(
        self, min_delay: Optional[float] = None, max_delay: Optional[float] = None
    ):
        """Add human-like random delay between actions."""
        if min_delay is None:
            min_delay = self.config["min_delay"]
        if max_delay is None:
            max_delay = self.config["max_delay"]

        # Type checker: we know these are now float values
        assert min_delay is not None and max_delay is not None
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        self.actions_performed += 1

    def human_scroll(self, direction: str = "down", distance: Optional[int] = None):
        """Perform human-like scrolling with variable speed and pauses."""
        if not self.driver:
            return

        if distance is None:
            distance = random.randint(300, 800)

        # Get current scroll position
        current_position = self.driver.execute_script("return window.pageYOffset;")

        if direction == "down":
            target_position = current_position + distance
        else:
            target_position = max(0, current_position - distance)

        # Scroll in small increments with random pauses
        steps = random.randint(5, 15)
        step_size = distance // steps

        for i in range(steps):
            if direction == "down":
                new_position = current_position + (i + 1) * step_size
            else:
                new_position = max(0, current_position - (i + 1) * step_size)

            # Smooth scroll with easing
            self.driver.execute_script(f"window.scrollTo(0, {new_position});")

            # Random pause between scroll steps
            pause = random.uniform(
                self.config["scroll_pause_min"], self.config["scroll_pause_max"]
            )
            time.sleep(pause)

            # Occasionally add longer pause (like human reading)
            if random.random() < 0.1:  # 10% chance
                time.sleep(random.uniform(1.0, 3.0))

        # Final scroll to exact position
        self.driver.execute_script(f"window.scrollTo(0, {target_position});")

        # Post-scroll pause
        self.random_delay(0.5, 1.5)

    def fast_scroll(self, direction: str = "down", distance: Optional[int] = None):
        """Perform fast scrolling with minimal delays for speed optimization."""
        if not self.driver:
            return

        if distance is None:
            distance = random.randint(400, 1000)  # Larger steps for faster scrolling

        # Get current scroll position
        current_position = self.driver.execute_script("return window.pageYOffset;")

        if direction == "down":
            target_position = current_position + distance
        else:
            target_position = max(0, current_position - distance)

        # Fast scroll with minimal steps and delays
        steps = random.randint(2, 5)  # Fewer steps for faster scrolling
        step_size = distance // steps

        for i in range(steps):
            if direction == "down":
                new_position = current_position + (i + 1) * step_size
            else:
                new_position = max(0, current_position - (i + 1) * step_size)

            # Direct scroll without easing
            self.driver.execute_script(f"window.scrollTo(0, {new_position});")

            # Minimal pause between scroll steps
            time.sleep(0.05)  # Very short delay

        # Final scroll to exact position
        self.driver.execute_script(f"window.scrollTo(0, {target_position});")

        # Minimal post-scroll pause
        time.sleep(0.1)

    def simulate_mouse_movement(self, element=None):
        """Simulate human-like mouse movement."""
        if not self.config["mouse_movement"] or not self.driver:
            return

        try:
            actions = ActionChains(self.driver)

            if element:
                # Move to specific element
                actions.move_to_element(element)
            else:
                # Random mouse movement
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)

            # Add some random mouse movements
            for _ in range(random.randint(1, 3)):
                actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))

            actions.perform()

        except Exception:
            # Silently fail for mouse movement simulation
            pass

    def human_type(self, element, text: str):
        """Simulate human-like typing with random delays."""
        if not self.config["random_typing"]:
            element.send_keys(text)
            return

        # Clear field first
        element.clear()
        self.random_delay(0.1, 0.3)

        # Type character by character with random delays
        for char in text:
            element.send_keys(char)
            # Random delay between characters (like human typing)
            delay = random.uniform(0.05, 0.15)
            time.sleep(delay)

            # Occasionally add longer pause (like human thinking)
            if random.random() < 0.05:  # 5% chance
                time.sleep(random.uniform(0.2, 0.5))

    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.user_agents)

    def get_random_window_size(self) -> tuple:
        """Get a random window size for fingerprint randomization."""
        return random.choice(self.window_sizes)

    def enhance_chrome_options(self, chrome_options: Options):
        """Enhance Chrome options with anti-detection features."""
        if not self.config["fingerprint_randomization"]:
            return

        # Enhanced anti-detection Chrome options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")

        # Random window size
        window_size = self.get_random_window_size()
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")

        # Random user agent
        user_agent = self.get_random_user_agent()
        chrome_options.add_argument(f"--user-agent={user_agent}")

        # Additional preferences to mask automation
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Remove automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

    def remove_automation_flags(self):
        """Remove automation flags and add human-like properties."""
        if not self.driver:
            return

        scripts = [
            # Remove webdriver property
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            # Add human-like properties
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            "Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})",
            # Override permissions
            "const originalQuery = window.navigator.permissions.query; window.navigator.permissions.query = (parameters) => (parameters.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : originalQuery(parameters));",
            # Add chrome runtime
            "window.chrome = {runtime: {}}",
            # Override iframe contentWindow
            "Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {get: function() {return window;}})",
        ]

        for script in scripts:
            try:
                self.driver.execute_script(script)
            except Exception:
                # Silently fail for script execution
                pass

    def human_click(self, element, scroll_to_element: bool = True):
        """Perform human-like click with mouse movement and delays."""
        if not self.driver:
            return

        try:
            # Scroll to element if requested
            if scroll_to_element:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    element,
                )
                self.random_delay(0.5, 1.0)

            # Simulate mouse movement
            self.simulate_mouse_movement(element)

            # Small delay before clicking
            self.random_delay(0.2, 0.5)

            # Click the element
            element.click()

        except Exception:
            # Fallback to direct click
            element.click()

    def human_fill_form(self, element, text: str, clear_first: bool = True):
        """Fill form fields with human-like behavior."""
        if not self.driver:
            return

        try:
            # Scroll to element
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element,
            )
            self.random_delay(0.5, 1.0)

            # Simulate mouse movement
            self.simulate_mouse_movement(element)

            # Click to focus
            element.click()
            self.random_delay(0.2, 0.5)

            # Fill with human-like typing
            self.human_type(element, text)

        except Exception:
            # Fallback to direct interaction
            if clear_first:
                element.clear()
            element.send_keys(text)

    def rotate_session(self):
        """Rotate session to avoid detection."""
        if not self.config["session_rotation"] or not self.driver:
            return

        try:
            # Clear cookies and cache
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")

            # Refresh page
            self.driver.refresh()
            self.random_delay(2, 4)

        except Exception:
            # Silently fail for session rotation
            pass

    def natural_page_navigation(self, url: str):
        """Navigate to page with human-like behavior."""
        if not self.driver:
            return

        try:
            # Random delay before navigation
            self.random_delay(1, 3)

            # Navigate to URL
            self.driver.get(url)

            # Wait for page to load
            self.random_delay(2, 4)

            # Simulate reading behavior
            self.random_delay(1, 2)

        except Exception:
            # Fallback to direct navigation
            self.driver.get(url)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get human-like behavior statistics."""
        if not self.session_start_time:
            return {}

        session_duration = datetime.now() - self.session_start_time

        return {
            "session_duration": str(session_duration),
            "actions_performed": self.actions_performed,
            "actions_per_minute": self.actions_performed
            / max(session_duration.total_seconds() / 60, 1),
            "human_config": self.config,
        }

    def update_config(self, **kwargs):
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value

    def enable_all_features(self):
        """Enable all human-like behavior features."""
        self.config.update(
            {
                "mouse_movement": True,
                "random_typing": True,
                "session_rotation": True,
                "fingerprint_randomization": True,
            }
        )

    def disable_all_features(self):
        """Disable all human-like behavior features."""
        self.config.update(
            {
                "mouse_movement": False,
                "random_typing": False,
                "session_rotation": False,
                "fingerprint_randomization": False,
            }
        )
