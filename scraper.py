import asyncio
import csv
import time
import os
import logging
import argparse
from typing import List, Dict
from mcp_use import MCPClient
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
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
    """Handles searching for potential LinkedIn profiles using DuckDuckGo"""

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
            reader = csv.DictReader(f, delimiter=";")
            return list(reader)

    async def gather_linkedin_info(
        self, input_csv: str, output_csv: str = "data/ddg_results.csv"
    ) -> None:
        """Gather potential LinkedIn profile information using DuckDuckGo search"""
        try:
            profiles = self._load_search_terms(input_csv)

            os.makedirs(os.path.dirname(output_csv), exist_ok=True)

            with open(output_csv, "w", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(
                    ["organization", "job_title", "name", "event", "ddg_search"]
                )

                for profile in profiles:
                    try:
                        self.logger.info(
                            f"Searching for LinkedIn info: {profile['name']} at {profile['organization']}"
                        )

                        ddg_session = await self.client.create_session("ddg-search")
                        query = f"{profile['name']} {profile['organization']} {profile['job_title']} LinkedIn profile"

                        response = await ddg_session.connector.call_tool(
                            "search", {"query": query, "max_results": 10}
                        )

                        if response and hasattr(response, "content"):
                            writer.writerow(
                                [
                                    profile["organization"],
                                    profile["job_title"],
                                    profile["name"],
                                    profile.get("event", ""),
                                    response.content[0].text
                                    if response.content
                                    else "",
                                ]
                            )
                            self.logger.info(
                                f"Found potential LinkedIn info for {profile['name']}"
                            )
                        else:
                            self.logger.warning(
                                f"No LinkedIn info found for {profile['name']}"
                            )
                            writer.writerow(
                                [
                                    profile["organization"],
                                    profile["job_title"],
                                    profile["name"],
                                    profile.get("event", ""),
                                    "",
                                ]
                            )

                        await asyncio.sleep(self.delay)

                    except Exception as e:
                        self.logger.error(f"Error processing {profile['name']}: {e}")
                        continue
                    finally:
                        if hasattr(ddg_session, "close"):
                            await ddg_session.close()

        except Exception as e:
            self.logger.error(f"Error in gather_linkedin_info: {e}")


class LinkedInScraper:
    """Handles scraping LinkedIn profiles"""

    def __init__(self, csv_path: str, delay_seconds: int = 180):
        self.delay = delay_seconds
        self.logger = logging.getLogger("linkedin_scraper")
        self.profiles = self._load_profiles(csv_path)

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
        """Load profiles from CSV file with unified column names"""
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            profiles = []
            for row in reader:
                name = row.get("name") or row.get("Name")
                url = row.get("url") or row.get("LinkedIn")

                if not name or not url:
                    self.logger.warning(f"Missing required columns in row: {row}")
                    continue

                profiles.append({"name": name, "url": url})
            return profiles

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
    parser = argparse.ArgumentParser(description="LinkedIn Profile Tools")
    parser.add_argument(
        "--mode",
        choices=["search", "scrape"],
        required=True,
        help="Mode: 'search' to find profiles using DuckDuckGo, 'scrape' to scrape found profiles",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input CSV file (search terms for search mode, profile URLs for scrape mode)",
    )
    parser.add_argument(
        "--output", type=str, help="Output CSV file (search results for search mode)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=30,
        help="Delay between requests in seconds (default: 30)",
    )
    args = parser.parse_args()

    if args.mode == "search":
        searcher = LinkedInProfileSearcher(delay_seconds=args.delay)
        asyncio.run(
            searcher.gather_linkedin_info(input_csv=args.input, output_csv=args.output)
        )
    else:  # scrape mode
        scraper = LinkedInScraper(args.input, delay_seconds=args.delay)
        asyncio.run(scraper.scrape_profiles())
