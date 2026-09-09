import pandas as pd
import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import re
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("speaker_scraper")


MARKDOWN_0 = """

![Ian Robertson](https://groundswellag.com/wp-content/uploads/2019/02/Ian-Robertson-2-rotated-e1745919970884-295x305.jpg)

## Ian Robertson

2025

Ian has a lifelong involvement in all things soil, growing up on an organic farm, working in various consultancy roles helping farmers understand their soils. Over the last 20 years Ian has developed one of the most detailed soil tests on the market, used throughout the UK and Europe enabling sustainable food production and landscape management

## My Sessions

03/07/2025 10:15 am-10:45 am

## Rainfall Simulator

[Affinity Stand PF X4](https://groundswellag.com/speakers/ian-robertson/#)

[VIEW PROFILE +\\
**Ian Robertson**](https://groundswellag.com/speakers/ian-robertson/)

[\+ view all](https://groundswellag.com/sessions/rainfall-simulator-thu/)

See the dramatic effect of two inches of rainfall on soils under different management regimes: no-till and cultivated, with and without cover and under permanent pasture

Demonstration

[READ MORE](https://groundswellag.com/sessions/rainfall-simulator-thu/)

02/07/2025 11:15 am-11:45 am

## Rainfall Simulator

[Affinity Stand PF X4](https://groundswellag.com/speakers/ian-robertson/#)

[VIEW PROFILE +\\
**Ian Robertson**](https://groundswellag.com/speakers/ian-robertson/)

[\+ view all](https://groundswellag.com/sessions/rainfall-simulator-wed/)

See the dramatic effect of two inches of rainfall on soils under different management regimes: no-till and cultivated, with and without cover and under permanent pasture

Demonstration

[READ MORE](https://groundswellag.com/sessions/rainfall-simulator-wed/)[READ MORE]

02/07/2025 12:00 pm-12:55 pm

## Uncovering Limiting Factors on Your Farm

[The Workshop Tent](https://groundswellag.com/speakers/ian-robertson/#)

[VIEW PROFILE +\\
**Abby Rose**](https://groundswellag.com/speakers/abby-rose/) [VIEW PROFILE +\\
**Tim Williams**](https://groundswellag.com/speakers/tim-williams/) [VIEW PROFILE +\\
**Ian Robertson**](https://groundswellag.com/speakers/ian-robertson/) [VIEW PROFILE +\\
**Jed Soleiman**](https://groundswellag.com/speakers/jed-soleiman/)

[\+ view all](https://groundswellag.com/sessions/uncovering-limiting-factors-on-your-farm/)

We will unpick how the physical, biological and mineral aspects of the soil impact each other. Learn how you can work with visual indicators, lab tests and other observations to troubleshoot and identify limiting factors on your farm. We will do this by focusing on 3-4 key talking points, such as a compaction layer in \[…\]

[READ MORE](https://groundswellag.com/sessions/uncovering-limiting-factors-on-your-farm/)

Groundswell Newsletter Sign Up

\* indicates required

Email Address \*

First Name

Last Name

Company

X

We use cookies to ensure that we give you the best experience on our website. If you continue to use this site we will assume that you are happy with it.[Ok](https://groundswellag.com/speakers/ian-robertson/#) [Ok](javascript:void(0);)

[iframe](https://static.addtoany.com/menu/sm.25.html#type=core&event=load)
"""

MARKDOWN_1 = """
![Simon Krämer](https://groundswellag.com/wp-content/uploads/2025/06/Simon-Kraemar-e1748855372122-295x305.png)

## Simon Krämer

2025

Simon Krämer is Executive Director and Policy Steward at the European Alliance for Regenerative Agriculture (EARA), a network of land stewards farming for systemic and holistic regeneration in Europe. He recently co-started a small farm in Sicily and works across civil, public, and private sectors to support incremental and radical paths toward regenerative agri-food systems through action research, novel accounting, and capacity building.

## My Sessions

02/07/2025 10:00 am-10:55 am

## Unity in Diversity: Europe's Farmer-led Agrifood Revolution

[Breakout Tent](https://groundswellag.com/speakers/simon-kraemer/#)

[VIEW PROFILE +\\
**Simon Krämer**](https://groundswellag.com/speakers/simon-kraemer/) [VIEW PROFILE +\\
**Anders Lerberg-Kopstad**](https://groundswellag.com/speakers/anders-lerberg-kopstad/) [VIEW PROFILE +\\
**Cathal Donnelly**](https://groundswellag.com/speakers/cathal-donnelly/) [VIEW PROFILE +\\
**Meghan Sapp**](https://groundswellag.com/speakers/meghan-sapp/) [VIEW PROFILE +\\
**Matteo Mazzola**](https://groundswellag.com/speakers/matteo-mazzola/) [VIEW PROFILE +\\
**Naomi Oakley**](https://groundswellag.com/speakers/naomi-oakley/)

[+ view all](https://groundswellag.com/sessions/unity-in-diversity-europes-farmer-led-agrifood-revolution/)

Europe's regenerative farmers are rising and uniting. This panel features farmer-leaders from Italy, Ireland, Norway, and Spain, and Simon Krämer, Executive Director of the European Alliance for Regenerative Agriculture (EARA), a network of land stewards working across policy, markets, finance, and education. EARA drives aligned farmer leadership through rapid consensus and a context-, place-, and \[…\]

[READ MORE](https://groundswellag.com/sessions/unity-in-diversity-europes-farmer-led-agrifood-revolution/)

Groundswell Newsletter Sign Up

* indicates required

Email Address *

First Name

Last Name

Company

X

We use cookies to ensure that we give you the best experience on our website. If you continue to use this site we will assume that you are happy with it.[Ok](https://groundswellag.com/speakers/simon-kraemer/#) [Ok](javascript:void(0);)

[iframe](https://static.addtoany.com/menu/sm.25.html#type=core&event=load)
"""


@dataclass
class SessionInfo:
    """Session information structure"""

    title: str = ""
    date: str = ""
    time: str = ""
    location: str = ""
    description: str = ""
    url: str = ""


@dataclass
class SpeakerProfile:
    """Minimal speaker data structure"""

    name: str
    url: str
    bio: str = ""
    sessions: Optional[List[SessionInfo]] = None

    def __post_init__(self):
        if self.sessions is None:
            self.sessions = []


class GroundswellScraper:
    def __init__(self, firecrawl_api_key: str, output_dir: str = "data/scraped"):
        self.api_key = firecrawl_api_key
        self.base_url = "https://api.firecrawl.dev/v1"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Rate limiting
        self.request_delay = 10.0  # seconds between requests
        self.max_retries = 3

    def scrape_speaker_page(self, url: str) -> Optional[Dict]:
        """Scrape a single speaker page using Firecrawl"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Firecrawl scrape endpoint
        scrape_data = {"url": url, "formats": ["markdown"], "onlyMainContent": True}

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/scrape",
                    headers=headers,
                    json=scrape_data,
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return data.get("data", {})
                    else:
                        logger.error(
                            f"Firecrawl error for {url}: {data.get('error', 'Unknown error')}"
                        )

                elif response.status_code == 429:
                    # Rate limited
                    wait_time = 2**attempt * 5  # Exponential backoff
                    logger.warning(
                        f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}"
                    )
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(f"HTTP {response.status_code} for {url}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url} (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                time.sleep(self.request_delay * (attempt + 1))

        return None

    def parse_speaker_data(self, raw_data: Dict, name: str, url: str) -> SpeakerProfile:
        """Extract bio and sessions from scraped data"""
        markdown = raw_data.get("markdown", "")
        lines = markdown.split("\n")

        bio_lines = []
        sessions = []

        # Extract bio (substantial paragraphs)
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip headers, empty lines, and navigation
            if not line or line.startswith("#") or len(line) < 50:
                i += 1
                continue

            # Look for bio content (longer paragraphs that aren't session info)
            if (
                len(line) > 80
                and "session" not in line.lower()
                and "tent" not in line.lower()
            ):
                bio_lines.append(line)

            # Extract sessions using the new function
            session_dicts = extract_sessions_from_markdown(markdown)
            sessions = [
                SessionInfo(
                    title=s.get("session_title", ""),
                    date=s.get("date", ""),
                    time=s.get("time", ""),
                    location=s.get("location", ""),
                    description=s.get("description", ""),
                    url=s.get("url", ""),
                )
                for s in session_dicts
            ]

            i += 1

        bio = " ".join(bio_lines)
        bio = bio.split(" **")[
            0
        ]  # remove the lines of other speakrs possibly mentioned

        return SpeakerProfile(name=name, url=url, bio=bio.strip(), sessions=sessions)

    def process_speakers(
        self,
        csv_path: str,
        start_index: int = 0,
        batch_size: int = 50,
        output_path: str = "groundswellag_speakers.csv",
    ):
        import pandas as pd

        df = pd.read_csv(csv_path, sep=";")
        total_speakers = len(df)
        logger.info(
            f"Processing {total_speakers} speakers, starting from index {start_index}"
        )

        while start_index < total_speakers:
            end_index = min(start_index + batch_size, total_speakers)
            batch = df.iloc[start_index:end_index]
            # Load existing names from the output file
            existing_names = get_existing_names(output_path)
            results = []
            for _, row in batch.iterrows():
                name = row["name"]
                url = row["speaker_page"] if "speaker_page" in row else row["url"]
                logger.info(f"Processing {name}")
                if name in existing_names:
                    logger.info(f"Skipping {name}: already present in {output_path}")
                    continue
                # Scrape the page
                raw_data = self.scrape_speaker_page(url)
                if raw_data:
                    profile = self.parse_speaker_data(raw_data, name, url)
                    results.append(profile)
                    bio_preview = (
                        profile.bio[:60] + "..."
                        if len(profile.bio) > 60
                        else profile.bio
                    )
                    sessions_info = (
                        f"{len(profile.sessions)} sessions"
                        if profile.sessions
                        else "no sessions"
                    )
                    logger.info(
                        f"✓ {name} - Bio: {bio_preview} | Sessions: {sessions_info}"
                    )
                else:
                    logger.error(f"✗ Failed to scrape {name}")
                    results.append(SpeakerProfile(name=name, url=url))
                # Rate limiting
                time.sleep(self.request_delay)
            # Save after each batch
            save_speakers_to_csv(results, output_path=output_path, max_sessions=3)
            logger.info(f"Saved batch results {batch} to: {output_path}")
            start_index = end_index
        logger.info("All batches complete.")


def main():
    """Process Groundswell speakers

    The final CSV is saved to the path specified by --output (default: groundswellag_speakers.csv in the current directory).
    """
    import os

    parser = argparse.ArgumentParser(
        description="Scrape speaker details from speaker pages."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/groundswellag_speaker_webpages.csv",
        help="Input CSV file with speaker URLs (default: data/groundswellag_speaker_webpages.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="groundswellag_speakers.csv",
        help="Output CSV file for speaker details (default: groundswellag_speakers.csv)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for scraping (default: 10)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start index for processing (default: 0)",
    )
    args = parser.parse_args()

    # Ensure output is in 'data' directory unless an absolute or custom path is provided
    output_path = args.output
    if not (
        output_path.startswith("/")
        or output_path.startswith("./")
        or "/" in output_path
    ):
        output_path = f"data/{output_path}"
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Configuration - get API key from environment variable
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    if not FIRECRAWL_API_KEY:
        logger.error("FIRECRAWL_API_KEY environment variable not set")
        logger.info("Set it with: export FIRECRAWL_API_KEY='your_actual_api_key'")
        return

    # Initialize scraper
    scraper = GroundswellScraper(FIRECRAWL_API_KEY, output_dir="data/scraped")

    try:
        scraper.process_speakers(
            args.input,
            start_index=args.start_index,
            batch_size=args.batch_size,
            output_path=output_path,
        )
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise


def test_parse_speaker_data():
    """
    Test the parsing logic on example results from Firecrawl
    """
    # Example Firecrawl markdown (as provided)
    # Simulate Firecrawl API MARKDOWN_1
    raw_data = {"markdown": MARKDOWN_0}
    name = "Simon Krämer"
    url = "https://groundswellag.com/speakers/simon-kraemer/"

    # Create a scraper instance (API key not needed for parsing)
    scraper = GroundswellScraper(firecrawl_api_key="dummy")
    profile = scraper.parse_speaker_data(raw_data, name, url)

    logger.info(f"Name: {profile.name}")
    logger.info(f"Bio: {profile.bio}")
    logger.info("Sessions:")
    for session in profile.sessions:
        logger.info(f"  Title: {session.title}")
        logger.info(f"  Date: {session.date}")
        logger.info(f"  Time: {session.time}")
        logger.info(f"  Location: {session.location}")
        logger.info(f"  Description: {session.description}")
        logger.info(f"  URL: {session.url}")
        logger.info("--------------------------------")


def extract_sessions_from_markdown(md, max_sessions=3):
    lines = md.split("\n")
    sessions = []
    i = 0
    # Find the line with '## My Sessions'
    while i < len(lines):
        if lines[i].strip().lower() == "## my sessions":
            break
        i += 1
    i += 1  # Move to the line after '## My Sessions'

    while i < len(lines) and len(sessions) < max_sessions:
        # Look for date/time line
        dt_line = lines[i].strip()
        dt_match = re.match(
            r"(\d{2}/\d{2}/\d{4})\s+(\d{1,2}:\d{2}\s*[ap]m-\d{1,2}:\d{2}\s*[ap]m)",
            dt_line,
            re.IGNORECASE,
        )
        if dt_match:
            date = dt_match.group(1)
            time = dt_match.group(2)
            title = ""
            location = ""
            url = ""
            description = ""
            # Look for session title (next ## ... line)
            j = i + 1
            while j < len(lines):
                line = lines[j].strip()
                if line.startswith("##"):
                    title = line.replace("##", "").strip()
                    j += 1
                    break
                j += 1
            # Look for location (first [text](url) after title)
            while j < len(lines):
                line = lines[j].strip()
                loc_match = re.match(r"\[(.*?)\]\((https?://[^\)]+)\)", line)
                if loc_match:
                    location = loc_match.group(1)
                    j += 1
                    break
                j += 1
            # Look for [+ view all] anchor and extract session URL and description
            while j < len(lines):
                line = lines[j].strip()
                url_match = re.search(
                    r"\[\\?\+\s*view\s*all\]\((https?://[^\)]+)\)", line, re.IGNORECASE
                )
                if url_match:
                    url = url_match.group(1)
                    j += 1
                    # Now, collect all subsequent lines as description until a header, link, or empty line
                    desc_lines = []
                    # Skip any empty lines immediately after [+ view all]
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    # Now collect all lines that are not headers or links or empty
                    while j < len(lines):
                        desc_line = lines[j].strip()
                        if (
                            not desc_line
                            or desc_line.startswith("##")
                            or re.match(r"\[.*?\]\(.*?\)", desc_line)
                        ):
                            break
                        desc_lines.append(desc_line)
                        j += 1
                    description = " ".join(desc_lines).strip()
                    break
                j += 1
            sessions.append(
                {
                    "session_title": title,
                    "date": date,
                    "time": time,
                    "location": location,
                    "url": url,
                    "description": description,
                }
            )
            i = j
        else:
            i += 1
    return sessions


def get_existing_names(output_path):
    if Path(output_path).exists():
        df = pd.read_csv(output_path)
        return set(df["name"])
    return set()


def save_speakers_to_csv(
    profiles, output_path="groundswellag_speakers.csv", max_sessions=3
):
    import pandas as pd
    from pathlib import Path

    # Read existing data if file exists
    if Path(output_path).exists():
        df_existing = pd.read_csv(output_path)
        existing_names = set(df_existing["name"])
    else:
        df_existing = pd.DataFrame()
        existing_names = set()

    # Build new rows, skipping duplicates
    new_rows = []
    for profile in profiles:
        if profile.name in existing_names:
            logger.info(f"Skipping {profile.name}: already present in {output_path}")
            continue  # Skip if already present
        row = {"name": profile.name, "bio": profile.bio, "url": profile.url}
        for i in range(1, max_sessions + 1):
            session = profile.sessions[i - 1] if len(profile.sessions) >= i else None
            row[f"session_title_{i}"] = session.title if session else ""
            row[f"session_date_{i}"] = session.date if session else ""
            row[f"session_time_{i}"] = session.time if session else ""
            row[f"session_location_{i}"] = session.location if session else ""
            row[f"session_description_{i}"] = session.description if session else ""
            row[f"session_url_{i}"] = session.url if session else ""
        new_rows.append(row)

    df_new = pd.DataFrame(new_rows)
    if not df_existing.empty:
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_final = df_new
    df_final.to_csv(output_path, index=False)


if __name__ == "__main__":
    # test_parse_speaker_data()
    main()
