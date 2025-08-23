#!/usr/bin/env python3
"""
Configuration package for Facebook Scraper
Contains Chrome driver and browser configuration utilities.
"""

from .config import (
    find_chrome_driver,
    find_chrome_binary,
    load_chrome_config_from_env,
    get_chrome_options,
    get_system_platform
)

__all__ = [
    "find_chrome_driver",
    "find_chrome_binary",
    "load_chrome_config_from_env",
    "get_chrome_options",
    "get_system_platform"
]
