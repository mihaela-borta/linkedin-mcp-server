# src/linkedin_mcp_server/drivers/chrome.py
"""
Chrome driver management for LinkedIn scraping.

This module handles the creation and management of Chrome WebDriver instances.
"""

import sys
from typing import Dict, Optional
import os
import logging
import inquirer  # type: ignore

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from linkedin_mcp_server.config import get_config
from linkedin_mcp_server.config.secrets import get_credentials
from linkedin_mcp_server.config.providers import clear_credentials_from_keyring

# Set up logging
logger = logging.getLogger("linkedin_mcp_server.chrome")

# Global driver storage to reuse sessions
active_drivers: Dict[str, webdriver.Chrome] = {}


def get_or_create_driver() -> Optional[webdriver.Chrome]:
    """
    Get existing driver or create a new one using the configured settings.

    Returns:
        Optional[webdriver.Chrome]: Chrome WebDriver instance or None if initialization fails
    """
    config = get_config()
    session_id = "default"

    # Return existing driver if available
    if session_id in active_drivers:
        return active_drivers[session_id]

    # Set up Chrome options
    chrome_options = Options()

    # Check if we're running in WSL
    is_wsl = (
        os.path.exists("/proc/version")
        and "microsoft" in open("/proc/version").read().lower()
    )

    if is_wsl:
        logger.info("Detected WSL environment - optimizing Chrome configuration")
        # WSL-specific optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # In WSL, check X11 availability but don't force headless mode
        if not config.chrome.headless:
            try:
                # Try to detect if X11 is available
                display = os.environ.get("DISPLAY")
                if not display:
                    logger.warning(
                        "No X11 display detected in WSL - browser may not be visible"
                    )
                    logger.info("To use visible mode in WSL:")
                    logger.info("1. Install an X11 server on Windows (e.g., VcXsrv)")
                    logger.info(
                        "2. Set DISPLAY environment variable (e.g., export DISPLAY=:0)"
                    )
                    logger.info("3. Run with --no-headless flag")
                else:
                    logger.info(f"X11 display detected: {display}")
            except Exception as e:
                logger.warning(f"Error checking X11: {e}")

    logger.info(
        f"Running browser in {'headless' if config.chrome.headless else 'visible'} mode"
    )
    if config.chrome.headless:
        chrome_options.add_argument("--headless=new")

    # Add additional options for stability
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    )

    # Add any custom browser arguments from config
    for arg in config.chrome.browser_args:
        chrome_options.add_argument(arg)

    # Initialize Chrome driver
    try:
        if config.chrome.chromedriver_path:
            logger.info(
                f"Using ChromeDriver at path: {config.chrome.chromedriver_path}"
            )
            service = Service(executable_path=config.chrome.chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            logger.info("Using auto-detected ChromeDriver")
            driver = webdriver.Chrome(options=chrome_options)

        # Add a page load timeout for safety
        driver.set_page_load_timeout(60)

        # Try to log in
        if login_to_linkedin(driver):
            logger.info("Successfully logged in to LinkedIn")
        elif config.chrome.non_interactive:
            # In non-interactive mode, if login fails, return None
            driver.quit()
            return None

        active_drivers[session_id] = driver
        return driver
    except Exception as e:
        error_msg = f"Error creating web driver: {e}"
        logger.error(error_msg)

        if config.chrome.non_interactive:
            logger.error("Failed to initialize driver in non-interactive mode")
            return None

        raise WebDriverException(error_msg)


def login_to_linkedin(driver: webdriver.Chrome) -> bool:
    """
    Log in to LinkedIn using stored credentials.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        bool: True if login was successful, False otherwise
    """
    config = get_config()
    credentials = get_credentials()

    if not credentials:
        logger.error("No credentials available")
        return False

    try:
        from linkedin_scraper import actions  # type: ignore

        actions.login(driver, credentials["email"], credentials["password"])
        return True
    except Exception as e:
        error_msg = f"Failed to login: {str(e)}"
        logger.error(error_msg)

        if not config.chrome.non_interactive:
            logger.warning(
                "You might need to confirm the login in your LinkedIn mobile app. "
                "Please try again and confirm the login."
            )

            if config.chrome.headless:
                logger.info(
                    "Try running with visible browser window to see what's happening: "
                    "uv run main.py --no-headless"
                )

            retry = inquirer.prompt(
                [
                    inquirer.Confirm(
                        "retry",
                        message="Would you like to try with different credentials?",
                        default=True,
                    ),
                ]
            )

            if retry and retry.get("retry", False):
                # Clear credentials from keyring and try again
                clear_credentials_from_keyring()
                # Try again with new credentials
                return login_to_linkedin(driver)

        return False


def initialize_driver() -> None:
    """
    Initialize the driver based on configuration.
    """
    config = get_config()

    if config.server.lazy_init:
        logger.info(
            "Using lazy initialization - driver will be created on first tool call"
        )
        if config.linkedin.email and config.linkedin.password:
            logger.info("LinkedIn credentials found in configuration")
        else:
            logger.info(
                "No LinkedIn credentials found - will look for stored credentials on first use"
            )
        return

    # Validate chromedriver can be found
    if config.chrome.chromedriver_path:
        logger.info(f"ChromeDriver found at: {config.chrome.chromedriver_path}")
        os.environ["CHROMEDRIVER"] = config.chrome.chromedriver_path
    else:
        logger.warning("ChromeDriver not found in common locations.")
        logger.info("Continuing with automatic detection...")
        logger.info(
            "Tip: install ChromeDriver and set the CHROMEDRIVER environment variable"
        )

    # Create driver and log in
    try:
        driver = get_or_create_driver()
        if driver:
            logger.info("Web driver initialized successfully")
        else:
            logger.error("Failed to initialize web driver.")
            sys.exit(1)
    except WebDriverException as e:
        logger.error(f"Failed to initialize web driver: {str(e)}")
        handle_driver_error()


def handle_driver_error() -> None:
    """
    Handle ChromeDriver initialization errors by providing helpful options.
    """
    config = get_config()

    questions = [
        inquirer.List(
            "chromedriver_action",
            message="What would you like to do?",
            choices=[
                ("Specify ChromeDriver path manually", "specify"),
                ("Get help installing ChromeDriver", "help"),
                ("Exit", "exit"),
            ],
        ),
    ]
    answers = inquirer.prompt(questions)

    if answers["chromedriver_action"] == "specify":
        path = inquirer.prompt(
            [inquirer.Text("custom_path", message="Enter ChromeDriver path")]
        )["custom_path"]

        if os.path.exists(path):
            # Update config with the new path
            config.chrome.chromedriver_path = path
            os.environ["CHROMEDRIVER"] = path
            logger.info(f"ChromeDriver path set to: {path}")
            # Try again with the new path
            initialize_driver()
        else:
            logger.warning(f"The specified path does not exist: {path}")
            initialize_driver()

    elif answers["chromedriver_action"] == "help":
        logger.info("\nChromeDriver Installation Guide:")
        logger.info(
            "1. Find your Chrome version: Chrome menu > Help > About Google Chrome"
        )
        logger.info(
            "2. Download matching ChromeDriver: https://chromedriver.chromium.org/downloads"
        )
        logger.info("3. Place ChromeDriver in a location on your PATH")
        logger.info("   - macOS/Linux: /usr/local/bin/ is recommended")
        logger.info(
            "   - Windows: Add to a directory in your PATH or specify the full path\n"
        )

        if inquirer.prompt(
            [inquirer.Confirm("try_again", message="Try again?", default=True)]
        )["try_again"]:
            initialize_driver()

    logger.error("ChromeDriver is required for this application to work properly.")
    sys.exit(1)
