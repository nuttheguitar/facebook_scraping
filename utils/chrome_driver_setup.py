#!/usr/bin/env python3
"""
Chrome Driver Setup for macOS
Handles ChromeDriver setup and management for Selenium WebDriver.
"""

import os
import platform
from typing import Callable, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# Import config to get the correct paths
try:
    from config.config import find_chrome_driver, find_chrome_binary, find_chrome_profile
except ImportError:
    # Fallback if config import fails
    def find_chrome_driver() -> Optional[str]:
        return None

    def find_chrome_binary() -> Optional[str]:
        return None

    def find_chrome_profile() -> Optional[str]:
        return None


class ChromeDriverSetup:
    """ChromeDriver setup and management for macOS."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.system = platform.system()
        self.machine = platform.machine()
        
        if self.system != "Darwin":
            raise RuntimeError("This ChromeDriver setup is designed for macOS only")
    
    def setup_driver(self, headless: bool = True, enhance_options: Optional[Callable] = None) -> webdriver.Chrome:
        """
        Setup Chrome WebDriver with macOS-optimized configuration.
        
        Args:
            headless (bool): Run in headless mode
            enhance_options (callable): Optional function to enhance Chrome options
            
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
        """
        options = self._create_chrome_options(headless)
        
        # Apply custom enhancements if provided
        if enhance_options:
            enhance_options(options)
        
        # Try different ChromeDriver sources
        driver = self._create_driver_with_fallback(options)
        
        if not driver:
            raise RuntimeError("Failed to create Chrome WebDriver")
        
        return driver
    
    def _create_chrome_options(self, headless: bool) -> Options:
        """Create Chrome options optimized for macOS."""
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
        # macOS-specific options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-agent={self.ua.random}")
        
        # macOS-specific preferences
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Try to set Chrome binary location from config
        chrome_binary = find_chrome_binary()
        if chrome_binary and os.path.exists(chrome_binary):
            options.binary_location = chrome_binary
            print(f"✅ Using Chrome binary from: {chrome_binary}")
        
        # Set up profile for persistent sessions
        self._setup_profile_options(options)
        
        return options
    
    def _setup_profile_options(self, options: Options) -> None:
        """Set up Chrome profile options for persistent sessions."""
        try:
            profile_path = find_chrome_profile()
            if profile_path and os.path.exists(profile_path):
                # Use existing profile directory
                options.add_argument(f"--user-data-dir={os.path.dirname(profile_path)}")
                options.add_argument(f"--profile-directory={os.path.basename(profile_path)}")
                print(f"✅ Using existing Chrome profile: {profile_path}")
            else:
                # Create a new profile directory in Downloads
                new_profile_dir = os.path.expanduser("~/Downloads/chrome-mac-arm64/ChromeProfile")
                if not os.path.exists(new_profile_dir):
                    os.makedirs(new_profile_dir, exist_ok=True)
                    print(f"✅ Created new Chrome profile directory: {new_profile_dir}")
                
                options.add_argument(f"--user-data-dir={new_profile_dir}")
                print(f"✅ Using new Chrome profile: {new_profile_dir}")
            
            # Additional profile-related options for better session persistence
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")
            
            # Keep cookies and session data
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.media_stream": 2,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.geolocation": 2,
            })
            
        except Exception as e:
            print(f"⚠️ Failed to setup profile options: {str(e)}")
            # Continue without profile if setup fails
    
    def check_profile_status(self) -> dict:
        """Check the status of Chrome profiles and return information."""
        try:
            profile_info = {
                "existing_profile": None,
                "new_profile": None,
                "profile_status": "unknown"
            }
            
            # Check for existing profile
            existing_profile = find_chrome_profile()
            if existing_profile and os.path.exists(existing_profile):
                profile_info["existing_profile"] = existing_profile
                profile_info["profile_status"] = "existing"
                
                # Check if profile is locked
                from utils.chrome_process_manager import ChromeProcessManager
                process_manager = ChromeProcessManager()
                is_unlocked = process_manager.wait_for_profile_unlock(existing_profile, max_wait=5)
                profile_info["profile_locked"] = not is_unlocked
                
                print(f"✅ Found existing profile: {existing_profile}")
                print(f"   Profile locked: {profile_info['profile_locked']}")
            else:
                # Check for new profile directory
                new_profile_dir = os.path.expanduser("~/Downloads/chrome-mac-arm64/ChromeProfile")
                if os.path.exists(new_profile_dir):
                    profile_info["new_profile"] = new_profile_dir
                    profile_info["profile_status"] = "new"
                    print(f"✅ Found new profile directory: {new_profile_dir}")
                else:
                    profile_info["profile_status"] = "none"
                    print("⚠️ No Chrome profile found")
            
            return profile_info
            
        except Exception as e:
            print(f"⚠️ Error checking profile status: {str(e)}")
            return {"profile_status": "error", "error": str(e)}
    
    def _create_driver_with_fallback(self, options: Options) -> Optional[webdriver.Chrome]:
        """Create Chrome driver with fallback options."""
        # Priority 1: Try config ChromeDriver path
        config_driver = self._try_config_chromedriver(options)
        if config_driver:
            return config_driver
        
        # Priority 2: Try system ChromeDriver
        system_driver = self._try_system_chromedriver(options)
        if system_driver:
            return system_driver
        
        # Priority 3: Try webdriver-manager
        webdriver_manager_driver = self._try_webdriver_manager(options)
        if webdriver_manager_driver:
            return webdriver_manager_driver
        
        # Priority 4: Try common macOS locations
        common_driver = self._try_common_locations(options)
        if common_driver:
            return common_driver
        
        return None
    
    def _try_config_chromedriver(self, options: Options) -> Optional[webdriver.Chrome]:
        """Try to use ChromeDriver from config file."""
        try:
            driver_path = find_chrome_driver()
            if driver_path and os.path.exists(driver_path):
                # Ensure executable permissions
                os.chmod(driver_path, 0o755)
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Using ChromeDriver from config: {driver_path}")
                return driver
        except Exception as e:
            print(f"⚠️ Config ChromeDriver failed: {str(e)}")
        
        return None
    
    def _try_system_chromedriver(self, options: Options) -> Optional[webdriver.Chrome]:
        """Try to use system ChromeDriver from PATH."""
        try:
            service = Service("chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Using system ChromeDriver from PATH")
            return driver
        except Exception as e:
            print(f"⚠️ System ChromeDriver failed: {str(e)}")
            return None
    
    def _try_webdriver_manager(self, options: Options) -> Optional[webdriver.Chrome]:
        """Try to use webdriver-manager."""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Using webdriver-manager ChromeDriver")
            return driver
        except Exception as e:
            print(f"⚠️ webdriver-manager failed: {str(e)}")
            return None
    
    def _try_common_locations(self, options: Options) -> Optional[webdriver.Chrome]:
        """Try common macOS ChromeDriver locations."""
        common_paths = [
            # Priority: Downloads directory (same as config)
            os.path.expanduser("~/Downloads/chromedriver-mac-arm64/chromedriver"),
            os.path.expanduser("~/Downloads/chromedriver-mac-x64/chromedriver"),
            os.path.expanduser("~/Downloads/chromedriver"),
            # System locations
            "/usr/local/bin/chromedriver",
            "/opt/homebrew/bin/chromedriver",
            "/usr/bin/chromedriver",
            os.path.expanduser("~/chromedriver"),
            "/Applications/chromedriver",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                try:
                    # Ensure executable permissions
                    os.chmod(path, 0o755)
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=options)
                    print(f"✅ Using ChromeDriver from: {path}")
                    return driver
                except Exception as e:
                    print(f"⚠️ ChromeDriver at {path} failed: {str(e)}")
                    continue
        
        return None
    
    def get_chrome_version(self) -> str:
        """Get Chrome version from system."""
        try:
            import subprocess
            
            # First try to get version from config binary
            chrome_binary = find_chrome_binary()
            if chrome_binary and os.path.exists(chrome_binary):
                try:
                    print(f"🔍 Checking Chrome version from config binary: {chrome_binary}")
                    result = subprocess.run(
                        [chrome_binary, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        print(f"✅ Chrome version from config binary: {version}")
                        # Extract version number
                        import re
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                        if match:
                            return match.group(1)
                except Exception as e:
                    print(f"⚠️ Failed to get version from config binary: {str(e)}")
            
            # macOS Chrome locations as fallback
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    try:
                        print(f"🔍 Checking Chrome version from: {chrome_path}")
                        result = subprocess.run(
                            [chrome_path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip()
                            print(f"✅ Chrome version from system: {version}")
                            # Extract version number
                            import re
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                            if match:
                                return match.group(1)
                    except Exception as e:
                        print(f"⚠️ Failed to get version from {chrome_path}: {str(e)}")
                        continue
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error getting Chrome version: {str(e)}")
            return "Unknown"
    
    def verify_config_paths(self) -> dict:
        """Verify that config paths are accessible and provide debugging info."""
        verification = {
            "chrome_driver": {
                "path": find_chrome_driver(),
                "exists": False,
                "executable": False,
                "permissions": None
            },
            "chrome_binary": {
                "path": find_chrome_binary(),
                "exists": False,
                "executable": False
            }
        }
        
        # Check ChromeDriver
        driver_path = verification["chrome_driver"]["path"]
        if driver_path:
            verification["chrome_driver"]["exists"] = os.path.exists(driver_path)
            if verification["chrome_driver"]["exists"]:
                verification["chrome_driver"]["executable"] = os.access(driver_path, os.X_OK)
                try:
                    stat = os.stat(driver_path)
                    verification["chrome_driver"]["permissions"] = oct(stat.st_mode)[-3:]
                except Exception:
                    verification["chrome_driver"]["permissions"] = "Unknown"
        
        # Check Chrome binary
        binary_path = verification["chrome_binary"]["path"]
        if binary_path:
            verification["chrome_binary"]["exists"] = os.path.exists(binary_path)
            if verification["chrome_binary"]["exists"]:
                verification["chrome_binary"]["executable"] = os.access(binary_path, os.X_OK)
        
        return verification

    def get_system_info(self) -> dict:
        """Get system information for debugging."""
        return {
            "system": self.system,
            "machine": self.machine,
            "chrome_version": self.get_chrome_version(),
            "python_version": platform.python_version(),
            "current_working_directory": os.getcwd(),
            "config_chrome_driver": find_chrome_driver(),
            "config_chrome_binary": find_chrome_binary(),
            "path_verification": self.verify_config_paths(),
            "profile_status": self.check_profile_status()
        }


def create_chrome_driver(headless: bool = True, enhance_options: Optional[Callable] = None) -> webdriver.Chrome:
    """
    Convenience function to create Chrome driver.
    
    Args:
        headless (bool): Run in headless mode
        enhance_options (callable): Optional function to enhance Chrome options
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    setup = ChromeDriverSetup()
    return setup.setup_driver(headless, enhance_options)


def create_chrome_driver_with_profile(headless: bool = False, profile_name: Optional[str] = None) -> webdriver.Chrome:
    """
    Create Chrome driver with profile management for persistent sessions.
    
    Args:
        headless (bool): Run in headless mode (default False for profile usage)
        profile_name (str): Optional specific profile name to use
        
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance with profile
    """
    setup = ChromeDriverSetup()
    
    # Check profile status first
    profile_info = setup.check_profile_status()
    print(f"📊 Profile Status: {profile_info['profile_status']}")
    
    # Create driver with profile options
    driver = setup.setup_driver(headless)
    
    if driver:
        print("✅ Chrome driver created successfully with profile management")
        print("🔐 Your Facebook login session should persist between runs!")
    else:
        print("❌ Failed to create Chrome driver with profile")
    
    return driver


def get_chrome_info() -> dict:
    """Get Chrome and system information."""
    setup = ChromeDriverSetup()
    return setup.get_system_info()
