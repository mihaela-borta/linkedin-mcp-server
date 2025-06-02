import asyncio
import csv
import time
import os
import logging
from typing import List, Dict
from mcp_use import MCPClient
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkedin_scraper")


def cleanup_chrome():
    """Clean up Chrome processes"""
    try:
        # Kill Chrome processes
        logger.info("Cleaning up Chrome processes...")
        subprocess.run(["pkill", "-f", "chrome"], check=False)
        subprocess.run(["pkill", "-f", "chromedriver"], check=False)
        time.sleep(2)  # Wait for processes to fully terminate
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")


# Clean up before starting
cleanup_chrome()


class LinkedInScraper:
    def __init__(self, csv_path: str, delay_seconds: int = 180):
        self.profiles = self._load_profiles(csv_path)
        self.delay = delay_seconds
        self.logger = logging.getLogger("linkedin_scraper")

        # Initialize MCP client with proper configuration
        config = {
            "mcpServers": {
                "linkedin-scraper": {
                    "command": "uv",
                    "args": [
                        "run",
                        "main.py",
                        "--no-setup",
                        "--debug",  # Enable debug logging
                    ],
                    "env": {
                        "LINKEDIN_EMAIL": os.environ["LINKEDIN_EMAIL"],
                        "LINKEDIN_PASSWORD": os.environ["LINKEDIN_PASSWORD"],
                        "CHROMEDRIVER": os.environ["CHROMEDRIVER"],
                    },
                }
            }
        }
        self.client = MCPClient.from_dict(config)
        self.logger.info("MCP client initialized")

    def _load_profiles(self, csv_path: str) -> List[Dict]:
        """Load profiles from CSV file"""
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)

    async def scrape_profiles(self):
        """Main scraping loop"""
        try:
            # Create and initialize session for the server
            self.logger.info("Creating MCP session...")
            session = await self.client.create_session("linkedin-scraper")
            self.logger.info("Connected to MCP server")

            for profile in self.profiles:
                try:
                    self.logger.info(
                        f"Scraping profile: {profile['name']} ({profile['url']})"
                    )

                    # Call the get_person_profile tool directly with the URL
                    response = await session.connector.call_tool(
                        "get_person_profile", {"linkedin_url": profile["url"]}
                    )

                    if response and hasattr(response, "content"):
                        result = response.content
                        if isinstance(result, dict):
                            if result.get("status") == "success":
                                self.logger.info(
                                    f"Successfully scraped {profile['name']}"
                                )
                                # Save profile data if needed
                                if "profile" in result:
                                    self.logger.info(
                                        f"Profile data saved: {result['profile'].get('name')}"
                                    )
                            else:
                                self.logger.error(
                                    f"Failed to scrape {profile['name']}: {result.get('message')}"
                                )
                        else:
                            self.logger.error(
                                f"Received invalid response for {profile['name']}"
                            )
                    else:
                        self.logger.error(
                            f"Received invalid response for {profile['name']}"
                        )

                    # Wait between requests
                    self.logger.info(
                        f"!!!!Waiting {self.delay} seconds before next request..."
                    )
                    await asyncio.sleep(self.delay)

                except Exception as e:
                    self.logger.error(f"Error scraping {profile['url']}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
        finally:
            # Close all sessions
            await self.client.close_all_sessions()
            self.logger.info("Closed connection to MCP server")


if __name__ == "__main__":
    print("🔍 LinkedIn Profile Scraper")
    print("=" * 40)
    print("Make sure:")
    print("1. You have the correct LinkedIn credentials in the script")
    print("2. The data/profiles.csv file exists with the required columns")
    print("=" * 40)
    print("To run this scraper:")
    print("1. Open a terminal")
    print("2. Run: uv run scraper.py")
    print("=" * 40)

    # Create scraper with a shorter delay for testing
    scraper = LinkedInScraper("data/profiles.csv", delay_seconds=30)

    # Run the scraper
    asyncio.run(scraper.scrape_profiles())
