import asyncio
import csv
import time
import os
import logging
import argparse
from typing import List, Dict, Optional
from mcp_use import MCPClient
import subprocess
import re

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporarily set to DEBUG to see what's happening
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


def find_start_index(
    profiles: List[Dict],
    resume_index: Optional[int] = None,
    resume_name: Optional[str] = None,
) -> int:
    """Find the starting index based on resume parameters"""
    if resume_index is not None:
        if 0 <= resume_index < len(profiles):
            logger.info(
                f"Resuming from index {resume_index}: {profiles[resume_index]['name']}"
            )
            return resume_index
        else:
            logger.warning(
                f"Resume index {resume_index} out of range (0-{len(profiles) - 1}), starting from beginning"
            )
            return 0

    if resume_name is not None:
        for i, profile in enumerate(profiles):
            if profile["name"].lower() == resume_name.lower():
                logger.info(f"Resuming from name '{resume_name}' at index {i}")
                return i
        logger.warning(f"Name '{resume_name}' not found, starting from beginning")
        return 0

    return 0


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

    def _extract_event_from_filename(self, filename: str) -> str:
        base = os.path.basename(filename)
        event = base.split("_")[0]
        return event

    def _load_search_terms(self, csv_path: str) -> List[Dict]:
        """Load search terms from CSV file, inferring event name if not present"""
        event_from_filename = self._extract_event_from_filename(csv_path)
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            profiles = []
            for row in reader:
                # Use event from CSV if present, else fallback to filename
                event = row.get("event") or event_from_filename
                row["event"] = event
                profiles.append(row)
            return profiles

    def _load_existing_results(self, output_csv: str) -> Dict[str, Dict]:
        """Load existing results from output CSV file"""
        existing_results = {}
        if os.path.exists(output_csv):
            try:
                with open(output_csv, "r") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    for row in reader:
                        name = row.get("name", "")
                        if name:
                            existing_results[name] = row
                            # Debug: log a few entries to see the structure
                            if len(existing_results) <= 3:
                                self.logger.debug(f"Loaded entry for {name}: {row}")
                self.logger.info(
                    f"Loaded {len(existing_results)} existing results from {output_csv}"
                )
            except Exception as e:
                self.logger.warning(f"Error loading existing results: {e}")
        return existing_results

    def _should_search_profile(
        self, profile: Dict, existing_results: Dict[str, Dict]
    ) -> bool:
        """Determine if we should search for this profile based on existing results"""
        name = profile.get("name", "")

        # If no entry exists for this name, we should search
        if name not in existing_results:
            self.logger.info(f"No existing entry found for {name}, will search")
            return True

        existing_entry = existing_results[name]
        job_title = existing_entry.get("job_title", "").strip()

        # Debug logging to see what we found
        self.logger.debug(f"Existing entry for {name}: {existing_entry}")

        # If job_title is empty or missing, we should search
        if not job_title:
            self.logger.info(f"Existing entry for {name} has no job_title, will search")
            return True

        # If we have a job_title, skip the search
        self.logger.info(
            f"Existing entry for {name} already has job_title: '{job_title}', skipping search"
        )
        return False

    async def gather_linkedin_info(
        self,
        input_csv: str,
        output_csv: str = "data/ddg_results.csv",
        resume_index: Optional[int] = None,
        resume_name: Optional[str] = None,
    ) -> None:
        """Gather potential LinkedIn profile information using DuckDuckGo search"""
        try:
            profiles = self._load_search_terms(input_csv)
            start_index = find_start_index(profiles, resume_index, resume_name)

            # Create a new output file with timestamp for safety
            base_name, ext = os.path.splitext(output_csv)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            new_output_csv = f"{base_name}_{timestamp}{ext}"

            # Load existing results to check what we already have
            existing_results = self._load_existing_results(output_csv)

            os.makedirs(os.path.dirname(new_output_csv), exist_ok=True)

            # Always create a new file
            mode = "w"
            write_header = True

            with open(new_output_csv, mode, newline="") as f:
                writer = csv.writer(f, delimiter=";")

                # Write header
                writer.writerow(
                    ["organization", "job_title", "name", "event", "ddg_search"]
                )

                for i, profile in enumerate(profiles[start_index:], start=start_index):
                    ddg_session = None  # Initialize ddg_session outside the try block
                    try:
                        name = profile.get("name", "")
                        self.logger.info(
                            f"[{i + 1}/{len(profiles)}] Processing: {name} at {profile['organization']}"
                        )

                        # Check if we should search for this profile
                        if not self._should_search_profile(profile, existing_results):
                            # Skip search, but write existing entry from the original file
                            existing_entry = existing_results.get(name, {})
                            writer.writerow(
                                [
                                    existing_entry.get(
                                        "organization", profile["organization"]
                                    ),
                                    existing_entry.get(
                                        "job_title", profile["job_title"]
                                    ),
                                    existing_entry.get("name", name),
                                    existing_entry.get(
                                        "event", profile.get("event", "")
                                    ),
                                    existing_entry.get("ddg_search", ""),
                                ]
                            )
                            self.logger.info(
                                f"Skipped search for {name}, copied existing entry"
                            )
                            continue

                        self.logger.info(
                            f"Searching for LinkedIn info: {name} at {profile['organization']}"
                        )

                        ddg_session = await self.client.create_session("ddg-search")
                        query = f"{name} {profile['organization']} {profile['job_title']} LinkedIn profile"

                        response = await ddg_session.connector.call_tool(
                            "search", {"query": query, "max_results": 10}
                        )

                        search_result = ""
                        if response and hasattr(response, "content"):
                            search_result = (
                                response.content[0].text if response.content else ""
                            )
                            self.logger.info(
                                f"Found potential LinkedIn info for {name}"
                            )
                        else:
                            self.logger.warning(f"No LinkedIn info found for {name}")

                        # Write the result
                        writer.writerow(
                            [
                                profile["organization"],
                                profile["job_title"],
                                name,
                                profile.get("event", ""),
                                search_result,
                            ]
                        )

                        # Update existing results for future checks
                        existing_results[name] = {
                            "organization": profile["organization"],
                            "job_title": profile["job_title"],
                            "name": name,
                            "event": profile.get("event", ""),
                            "ddg_search": search_result,
                        }

                        await asyncio.sleep(self.delay)

                    except Exception as e:
                        self.logger.error(
                            f"Error processing {profile.get('name', 'unknown')}: {e}"
                        )
                        continue
                    finally:
                        if ddg_session and hasattr(ddg_session, "close"):
                            await ddg_session.close()

            self.logger.info(f"Results saved to: {new_output_csv}")

        except Exception as e:
            self.logger.error(f"Error in gather_linkedin_info: {e}")


class LinkedInScraper:
    """Handles scraping LinkedIn profiles"""

    def __init__(self, csv_path: str, delay_seconds: int = 180):
        self.delay = delay_seconds
        self.logger = logging.getLogger("linkedin_scraper")
        self.profiles = self._load_profiles(csv_path)
        self.event = self._extract_event_from_filename(csv_path)

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

    def _sanitize_event_name(self, event_name: str) -> str:
        # Lowercase, replace spaces with underscores, remove non-alphanum/underscore
        event = event_name.lower().replace(" ", "_")
        event = re.sub(r"[^a-z0-9_]", "", event)
        return event

    def _extract_event_from_filename(self, filename: str) -> str:
        base = os.path.basename(filename)
        event = base.split("_")[0]
        return event

    def _load_profiles(self, csv_path: str) -> List[Dict]:
        """Load profiles from CSV file with unified column names and event name"""
        event_from_filename = self._extract_event_from_filename(csv_path)
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            profiles = []
            for row in reader:
                name = row.get("name") or row.get("Name")
                url = row.get("url") or row.get("LinkedIn")
                event = row.get("event") or event_from_filename
                if not name or not url:
                    self.logger.warning(f"Missing required columns in row: {row}")
                    continue
                profiles.append({"name": name, "url": url, "event": event})
            return profiles

    def linkedin_slug(self, url: str) -> str:
        return url.rstrip("/").split("/")[-1]

    async def scrape_profiles(
        self, resume_index: Optional[int] = None, resume_name: Optional[str] = None
    ):
        """Main scraping loop"""
        try:
            start_index = find_start_index(self.profiles, resume_index, resume_name)
            self.logger.info("Creating MCP session...")
            session = await self.client.create_session("linkedin-scraper")
            self.logger.info("Connected to MCP server")

            for i, profile in enumerate(self.profiles[start_index:], start=start_index):
                try:
                    self.logger.info(
                        f"[{i + 1}/{len(self.profiles)}] Scraping profile: {profile['name']} ({profile['url']})"
                    )

                    # Always pass sanitized event_name to the MCP tool
                    event_name = self._sanitize_event_name(
                        profile.get("event", self.event)
                    )
                    # Use LinkedIn slug for file existence check
                    slug = self.linkedin_slug(profile["url"])
                    storage_dir = os.path.expanduser(
                        os.path.join("~/linkedin_data", event_name)
                    )
                    filename = f"{slug}.json"
                    save_path = os.path.join(storage_dir, filename)
                    if os.path.exists(save_path):
                        self.logger.info(
                            f"Profile already exists for {profile['name']} (slug: {slug}) at {save_path}, skipping scrape."
                        )
                        self.logger.info(
                            f"Already have scraped profile for {profile['name']} (event: {event_name}, slug: {slug}), skipping."
                        )
                        continue

                    response = await session.connector.call_tool(
                        "get_person_profile",
                        {"linkedin_url": profile["url"], "event_name": event_name},
                    )

                    if response and hasattr(response, "content"):
                        result = response.content
                        if isinstance(result, dict):
                            if result.get("status") == "success":
                                self.logger.info(
                                    f"Successfully scraped {profile['name']} (slug: {slug})"
                                )
                                # No need to save locally; MCP server handles saving
                                if "profile" in result:
                                    self.logger.info(
                                        f"Profile data saved: {result['profile'].get('name')} (slug: {slug})"
                                    )
                            else:
                                self.logger.error(
                                    f"Failed to scrape {profile['name']} (slug: {slug}): {result.get('message')}"
                                )
                        else:
                            self.logger.error(
                                f"Received invalid response for {profile['name']} (slug: {slug})"
                            )
                    else:
                        self.logger.error(
                            f"Received invalid response for {profile['name']} (slug: {slug})"
                        )

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
            await self.client.close_all_sessions()
            self.logger.info("Closed connection to MCP server")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Profile Tools")
    parser.add_argument(
        "--mode",
        choices=["search", "scrape"],
        required=True,
        help="Mode: 'search' to search for LinkedIn profile info using DuckDuckGo, 'scrape' to scrape found profiles",
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
    parser.add_argument(
        "--resume-index",
        type=int,
        help="Resume processing from this index (0-based)",
    )
    parser.add_argument(
        "--resume-name",
        type=str,
        help="Resume processing from this person's name (case-insensitive)",
    )
    args = parser.parse_args()

    if args.mode == "search":
        searcher = LinkedInProfileSearcher(delay_seconds=args.delay)
        asyncio.run(
            searcher.gather_linkedin_info(
                input_csv=args.input,
                output_csv=args.output,
                resume_index=args.resume_index,
                resume_name=args.resume_name,
            )
        )
    else:  # scrape mode
        scraper = LinkedInScraper(args.input, delay_seconds=args.delay)
        asyncio.run(
            scraper.scrape_profiles(
                resume_index=args.resume_index, resume_name=args.resume_name
            )
        )
