#!/usr/bin/env python3
"""
Chrome Process Manager Module

Handles Chrome process identification, termination, and management for Selenium automation.
This module provides clean separation of concerns for Chrome process operations.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
import psutil


class ChromeProcessManager:
    """Manages Chrome processes specifically related to Selenium/ChromeDriver automation."""

    # Selenium-specific Chrome command line arguments for process identification
    SELENIUM_CHROME_INDICATORS = [
        "--remote-debugging-port",
        "--user-data-dir",
        "--profile-directory",
        "--no-first-run",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-sync",
        "--disable-translate",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--disable-features=VizDisplayCompositor",
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Chrome Process Manager.

        Args:
            logger: Optional logger instance. If None, creates a basic logger.
        """
        self.logger = logger or self._create_default_logger()

    def _create_default_logger(self) -> logging.Logger:
        """Create a default logger if none provided."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def terminate_selenium_chrome_sessions(self) -> bool:
        """Terminate existing Chrome processes specifically related to Selenium/ChromeDriver.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log current process details before cleanup
            self.logger.info("Current Chrome process status before cleanup:")
            process_details = self.get_chrome_process_details()

            for proc_type, processes in process_details.items():
                if processes:
                    self.logger.info(f"  {proc_type}: {len(processes)} processes")
                    for proc in processes[:3]:  # Show first 3 processes
                        self.logger.info(f"    PID {proc['pid']}: {proc['name']}")
                    if len(processes) > 3:
                        self.logger.info(f"    ... and {len(processes) - 3} more")
                else:
                    self.logger.info(f"  {proc_type}: 0 processes")

            # Find and terminate only Chrome processes related to Selenium/ChromeDriver
            selenium_chrome_processes = []
            chromedriver_processes = []

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_name = proc.info["name"].lower()
                    cmdline = proc.info.get("cmdline", [])

                    # Check for ChromeDriver processes
                    if "chromedriver" in proc_name:
                        chromedriver_processes.append(proc)
                        continue

                    # Check for Chrome processes that are likely from Selenium
                    if "chrome" in proc_name:
                        if self._is_selenium_chrome_process(cmdline):
                            selenium_chrome_processes.append(proc)

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            total_selenium_processes = len(selenium_chrome_processes) + len(
                chromedriver_processes
            )

            if total_selenium_processes > 0:
                self.logger.info(
                    f"Found {len(selenium_chrome_processes)} Selenium Chrome processes and {len(chromedriver_processes)} ChromeDriver processes, terminating..."
                )

                # Terminate ChromeDriver processes first
                for proc in chromedriver_processes:
                    try:
                        proc.terminate()
                        self.logger.info(
                            f"Terminated ChromeDriver process: PID {proc.info['pid']}"
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Terminate Selenium Chrome processes
                for proc in selenium_chrome_processes:
                    try:
                        proc.terminate()
                        self.logger.info(
                            f"Terminated Selenium Chrome process: PID {proc.info['pid']}"
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Wait a bit for processes to terminate
                time.sleep(2)

                # Force kill any remaining processes
                for proc in chromedriver_processes + selenium_chrome_processes:
                    try:
                        if proc.is_running():
                            proc.kill()
                            self.logger.info(
                                f"Force killed process: PID {proc.info['pid']}"
                            )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                self.logger.info("Selenium Chrome processes terminated successfully")

                # Log process status after cleanup
                self.logger.info("Chrome process status after cleanup:")
                process_details_after = self.get_chrome_process_details()

                for proc_type, processes in process_details_after.items():
                    if processes:
                        self.logger.info(f"  {proc_type}: {len(processes)} processes")
                    else:
                        self.logger.info(f"  {proc_type}: 0 processes")

                return True
            else:
                self.logger.info("No Selenium Chrome processes found")
                return True

        except Exception as e:
            self.logger.warning(
                f"Failed to terminate Selenium Chrome processes: {str(e)}"
            )
            return False

    def check_selenium_chrome_status(self) -> bool:
        """Check if Selenium Chrome is currently running.

        Returns:
            bool: True if Selenium Chrome is running, False otherwise
        """
        try:
            selenium_chrome_running = False
            chromedriver_running = False

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_name = proc.info["name"].lower()
                    cmdline = proc.info.get("cmdline", [])

                    # Check for ChromeDriver processes
                    if "chromedriver" in proc_name:
                        chromedriver_running = True
                        continue

                    # Check for Chrome processes that are likely from Selenium
                    if "chrome" in proc_name:
                        if self._is_selenium_chrome_process(cmdline):
                            selenium_chrome_running = True

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            if selenium_chrome_running:
                self.logger.info("Selenium Chrome is currently running")
            else:
                self.logger.info("No Selenium Chrome processes found")

            if chromedriver_running:
                self.logger.info("ChromeDriver is currently running")
            else:
                self.logger.info("No ChromeDriver processes found")

            return selenium_chrome_running or chromedriver_running

        except Exception as e:
            self.logger.warning(f"Error checking Selenium Chrome status: {str(e)}")
            return False

    def get_chrome_process_details(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed information about running Chrome processes for debugging.

        Returns:
            Dict containing categorized Chrome processes
        """
        try:
            selenium_chrome_processes = []
            chromedriver_processes = []
            regular_chrome_processes = []

            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    proc_name = proc.info["name"].lower()
                    cmdline = proc.info.get("cmdline", [])

                    # Check for ChromeDriver processes
                    if "chromedriver" in proc_name:
                        chromedriver_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cmdline": cmdline,
                                "create_time": proc.info["create_time"],
                            }
                        )
                        continue

                    # Check for Chrome processes
                    if "chrome" in proc_name:
                        if self._is_selenium_chrome_process(cmdline):
                            selenium_chrome_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cmdline": cmdline,
                                    "create_time": proc.info["create_time"],
                                    "type": "selenium",
                                }
                            )
                        else:
                            regular_chrome_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cmdline": cmdline,
                                    "create_time": proc.info["create_time"],
                                    "type": "regular",
                                }
                            )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            return {
                "selenium_chrome": selenium_chrome_processes,
                "chromedriver": chromedriver_processes,
                "regular_chrome": regular_chrome_processes,
            }

        except Exception as e:
            self.logger.warning(f"Error getting Chrome process details: {str(e)}")
            return {"selenium_chrome": [], "chromedriver": [], "regular_chrome": []}

    def _is_selenium_chrome_process(self, cmdline: List[str]) -> bool:
        """Check if a Chrome process is Selenium-related based on command line arguments.

        Args:
            cmdline: List of command line arguments

        Returns:
            bool: True if Selenium-related, False otherwise
        """
        if not cmdline:
            return False

        # Check if this Chrome process has Selenium-specific arguments
        is_selenium_chrome = any(
            indicator in " ".join(cmdline)
            for indicator in self.SELENIUM_CHROME_INDICATORS
        )

        # Also check for remote debugging port (common Selenium indicator)
        has_remote_debug = any("--remote-debugging-port" in arg for arg in cmdline)

        return is_selenium_chrome or has_remote_debug

    def wait_for_profile_unlock(self, profile_dir: str, max_wait: int = 10) -> bool:
        """Wait for the profile directory to be unlocked by checking for lock files.

        Args:
            profile_dir: Path to the Chrome profile directory
            max_wait: Maximum time to wait in seconds

        Returns:
            bool: True if unlocked, False if still locked after timeout
        """
        try:
            # Check for common lock files
            lock_files = [
                os.path.join(os.path.dirname(profile_dir), "SingletonLock"),
                os.path.join(profile_dir, "lockfile"),
                os.path.join(profile_dir, ".lock"),
            ]

            start_time = time.time()
            while time.time() - start_time < max_wait:
                locked = False
                for lock_file in lock_files:
                    if os.path.exists(lock_file):
                        try:
                            # Try to remove the lock file
                            os.remove(lock_file)
                            self.logger.info(f"Removed lock file: {lock_file}")
                        except (OSError, PermissionError):
                            locked = True
                            break

                if not locked:
                    self.logger.info("Profile directory is unlocked")
                    return True

                self.logger.info("Profile directory is locked, waiting...")
                time.sleep(1)

            self.logger.warning(
                f"Profile directory still locked after {max_wait} seconds"
            )
            return False

        except Exception as e:
            self.logger.warning(f"Error checking profile lock status: {str(e)}")
            return False

    @classmethod
    def add_selenium_indicator(cls, indicator: str) -> bool:
        """Add a new Selenium indicator to the list.

        Args:
            indicator: New indicator string to add

        Returns:
            bool: True if added, False if already exists
        """
        if indicator not in cls.SELENIUM_CHROME_INDICATORS:
            cls.SELENIUM_CHROME_INDICATORS.append(indicator)
            return True
        return False

    @classmethod
    def remove_selenium_indicator(cls, indicator: str) -> bool:
        """Remove a Selenium indicator from the list.

        Args:
            indicator: Indicator string to remove

        Returns:
            bool: True if removed, False if not found
        """
        if indicator in cls.SELENIUM_CHROME_INDICATORS:
            cls.SELENIUM_CHROME_INDICATORS.remove(indicator)
            return True
        return False

    @classmethod
    def get_selenium_indicators(cls) -> List[str]:
        """Get the current list of Selenium indicators.

        Returns:
            List of current Selenium indicators
        """
        return cls.SELENIUM_CHROME_INDICATORS.copy()

    def cleanup(self):
        """Clean up any resources used by the process manager."""
        # Currently no cleanup needed, but method available for future use
        pass
