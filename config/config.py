#!/usr/bin/env python3
"""
Configuration file for Facebook Scraper
Contains all Chrome driver and browser path configurations
"""

import os

# Chrome Driver Configuration
CHROME_DRIVER_PATHS = {
    "mac": ["/Users/nuttakan.w/Downloads/chromedriver-mac-arm64/chromedriver"]
}

# Chrome Browser Binary Paths
CHROME_BINARY_PATHS = {
    "mac": [
        "/Users/nuttakan.w/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    ]
}

# Chrome Options Configuration
CHROME_OPTIONS = {
    "headless": False,  # Set to False to show UI by default
    "no_sandbox": False,
    "disable_dev_shm_usage": False,
    "disable_gpu": False,
    "window_size": "1920,1080",
    "disable_blink_features": "AutomationControlled",
    "exclude_switches": ["enable-automation"],
    "use_automation_extension": False,
}


def get_system_platform():
    """Get the current operating system platform."""
    import platform

    system = platform.system().lower()
    if system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def find_chrome_driver():
    """Find the Chrome driver executable path."""
    platform = get_system_platform()

    for path in CHROME_DRIVER_PATHS[platform]:
        if os.path.exists(path) or os.system(f"which {path}") == 0:
            return path

    # If no driver found, return None to use webdriver_manager
    return None


def find_chrome_binary():
    """Find the Chrome browser binary path."""
    platform = get_system_platform()

    for path in CHROME_BINARY_PATHS[platform]:
        if os.path.exists(path):
            return path

    return None


def get_chrome_options():
    """Get Chrome options configuration."""
    return CHROME_OPTIONS.copy()


# Environment-specific overrides
def load_chrome_config_from_env():
    """Load Chrome configuration from environment variables if they exist."""
    config = get_chrome_options()

    # Override with environment variables if they exist
    if os.getenv("CHROME_DRIVER_PATH"):
        config["driver_path"] = os.getenv("CHROME_DRIVER_PATH")

    if os.getenv("CHROME_BINARY_PATH"):
        config["binary_location"] = os.getenv("CHROME_BINARY_PATH")

    chrome_headless = os.getenv("CHROME_HEADLESS")
    if chrome_headless:
        config["headless"] = chrome_headless.lower() == "true"

    return config
