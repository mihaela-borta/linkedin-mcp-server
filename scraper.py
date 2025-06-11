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


class LinkedInProfileSearcher:
    """Handles searching for LinkedIn profiles using DuckDuckGo"""

    def __init__(self, delay_seconds: int = 30):
        self.delay = delay_seconds
        self.logger = logging.getLogger("linkedin_scraper")

        # Initialize DuckDuckGo MCP client
        config = {
            "mcpServers": {
                "ddg-search": {"command": "uvx", "args": ["duckduckgo-mcp-server"]}
            }
        }
        self.client = MCPClient.from_dict(config)
        self.logger.info("DuckDuckGo MCP client initialized")

    def _load_search_terms(self, csv_path: str) -> List[Dict]:
        """Load search terms from CSV file"""
        with open(csv_path, "r") as f:
            reader = csv.DictReader(
                f, delimiter=";"
            )  # Note: using semicolon as delimiter
            return list(reader)

    async def search_profile(
        self, name: str, organization: str, title: str
    ) -> str | None:
        """Search for a LinkedIn profile using DuckDuckGo"""
        try:
            # Create DuckDuckGo session
            ddg_session = await self.client.create_session("ddg-search")

            # Construct search query
            query = f"{name} {organization} {title} LinkedIn profile"
            self.logger.info(f"Searching for: {query}")

            # Search for profile
            response = await ddg_session.connector.call_tool(
                "search", {"query": query, "max_results": 10}
            )

            self.logger.info(f"Results: {response}")

            if response and hasattr(response, "content"):
                # The response is a text content with URLs
                text_content = response.content[0].text

                # Get organization name parts to filter out
                org_lower = organization.lower()
                org_prefix = org_lower[:4] if len(org_lower) >= 4 else org_lower

                # First try to find a LinkedIn profile URL
                if "/in/" in text_content:
                    # Find all occurrences of LinkedIn profile URLs
                    start = 0
                    while True:
                        start = text_content.find("https://www.linkedin.com/in/", start)
                        if start == -1:
                            break

                        # Find the end of the URL
                        end = text_content.find(" ", start)
                        if end == -1:
                            end = text_content.find("\n", start)
                        if end == -1:
                            end = len(text_content)

                        profile_url = text_content[start:end].strip()

                        # Check if this is a company profile
                        if (
                            org_lower not in profile_url.lower()
                            and org_prefix not in profile_url.lower()
                        ):
                            self.logger.info(f"Found LinkedIn profile: {profile_url}")
                            return profile_url

                        start = end  # Move past this URL to find the next one

                # If no profile URL found, try to find a post URL and extract profile
                if "/posts/" in text_content:
                    start = text_content.find("https://www.linkedin.com/posts/")
                    if start != -1:
                        end = text_content.find("_", start)
                        if end != -1:
                            # Extract the profile part from the post URL
                            profile_url = text_content[start:end].replace(
                                "/posts/", "/in/"
                            )
                            self.logger.info(
                                f"Found LinkedIn profile from post: {profile_url}"
                            )
                            return profile_url

            return None

        except Exception as e:
            self.logger.error(f"Error searching for profile: {e}")
            return None
        finally:
            if hasattr(ddg_session, "close"):
                await ddg_session.close()

    async def search_and_save_profiles(
        self, input_csv: str, output_csv: str = "data/profiles.csv"
    ):
        """Search for profiles and save URLs to CSV"""
        self.logger.info("Starting profile search...")

        # Load search terms
        profiles = self._load_search_terms(input_csv)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)

        # Open output CSV file
        with open(output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "url"])  # Write header

            for profile in profiles:
                try:
                    self.logger.info(f"Searching for profile: {profile['name']}")
                    linkedin_url = await self.search_profile(
                        profile["name"], profile["organization"], profile["title"]
                    )

                    if linkedin_url:
                        writer.writerow([profile["name"], linkedin_url])
                        self.logger.info(
                            f"Found profile for {profile['name']}: {linkedin_url}"
                        )
                    else:
                        self.logger.warning(f"No profile found for {profile['name']}")

                    # Wait between searches to avoid rate limiting
                    await asyncio.sleep(self.delay)

                except Exception as e:
                    self.logger.error(f"Error processing {profile['name']}: {e}")
                    continue


class LinkedInScraper:
    """Handles scraping LinkedIn profiles"""

    def __init__(self, csv_path: str, delay_seconds: int = 180):
        self.profiles = self._load_profiles(csv_path)
        self.delay = delay_seconds
        self.logger = logging.getLogger("linkedin_scraper")

        # Initialize LinkedIn MCP client
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
        self.logger.info("LinkedIn MCP client initialized")

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
                        f"Waiting {self.delay} seconds before next request..."
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
    print("2. The data/profiles_search_terms.csv file exists with the required columns")
    print("=" * 40)
    print("To run this scraper:")
    print("1. Open a terminal")
    print("2. Run: uv run scraper.py")
    print("=" * 40)

    # First search for profiles
    searcher = LinkedInProfileSearcher(delay_seconds=30)
    asyncio.run(
        searcher.search_and_save_profiles(
            input_csv="data/profiles_search_terms.csv", output_csv="data/profiles_1.csv"
        )
    )

    # Then scrape the found profiles
    # scraper = LinkedInScraper("data/profiles.csv", delay_seconds=30)
    # asyncio.run(scraper.scrape_profiles())
