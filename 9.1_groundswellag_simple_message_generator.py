#!/usr/bin/env python3
"""
Simple LinkedIn outreach message generator for Groundswell speakers.
Loads CSV with LinkedIn URLs, extracts slugs, and scrapes missing profiles automatically.
"""

import json
import os
import logging
import argparse
import csv
import asyncio
from anthropic import Anthropic
from typing import Dict, List
from utils import (
    clean_string,
    create_batch_job,
    poll_for_batch_completion,
    download_results_file,
    json_to_csv,
)
import sys

# Import the LinkedInScraper class
from mcp_use import MCPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("simple_message_generator")


def linkedin_slug(url: str) -> str:
    """Extract LinkedIn slug from URL (copied from LinkedInScraper)"""
    return url.rstrip("/").split("/")[-1]


def extract_event_from_filename(filename: str) -> str:
    """Extract event name from filename"""
    base = os.path.basename(filename)
    event = base.split("_")[0]
    return event


def sanitize_event_name(event_name: str) -> str:
    """Sanitize event name for directory structure (copied from LinkedInScraper)"""
    import re
    event = event_name.lower().replace(" ", "_")
    event = re.sub(r"[^a-z0-9_]", "", event)
    return event


def load_speakers_from_csv(csv_file: str) -> List[Dict]:
    """Load speakers from CSV file with LinkedIn URLs"""
    speakers = []
    try:
        event_name = extract_event_from_filename(csv_file)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            reader.fieldnames = [col.lower() for col in reader.fieldnames]
            
            for row in reader:
                speaker = {
                    'name': row.get('name', ''),
                    'bio': row.get('speaker_bio', ''),
                    'detailed_profile': row.get('detailed_profile', ''),
                    'selected_sessions': row.get('selected_session', ''),
                    'linkedin_url': row.get('linkedin', ''),
                    'event': event_name
                }
                
                if not speaker['name'] or not speaker['linkedin_url']:
                    logger.warning(f"Skipping speaker with missing name or LinkedIn URL: {row}")
                    continue
                    
                speakers.append(speaker)
                
        logger.info(f"Loaded {len(speakers)} speakers from {csv_file} (event: {event_name})")
        return speakers
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        raise


async def scrape_missing_linkedin_profile(
    linkedin_url: str, 
    event_name: str, 
    speaker_name: str
) -> bool:
    """Scrape a missing LinkedIn profile using the MCP server"""
    try:
        config = {
            "mcpServers": {
                "linkedin-scraper": {
                    "command": "uv",
                    "args": [
                        "run",
                        "main.py",
                        "--no-setup",
                        "--debug",
                    ],
                    "env": {
                        "LINKEDIN_EMAIL": os.environ["LINKEDIN_EMAIL"],
                        "LINKEDIN_PASSWORD": os.environ["LINKEDIN_PASSWORD"],
                        "CHROMEDRIVER": os.environ["CHROMEDRIVER"],
                    },
                }
            }
        }
        
        client = MCPClient.from_dict(config)
        logger.info(f"Initializing LinkedIn MCP client for {speaker_name}")
        
        try:
            session = await client.create_session("linkedin-scraper")
            logger.info(f"Connected to LinkedIn MCP server for {speaker_name}")
            
            sanitized_event = sanitize_event_name(event_name)
            
            response = await session.connector.call_tool(
                "get_person_profile",
                {"linkedin_url": linkedin_url, "event_name": sanitized_event},
            )
            
            if response and hasattr(response, "content"):
                result = response.content
                
                # Handle the MCP response structure: list containing TextContent with JSON text
                if isinstance(result, list) and len(result) > 0:
                    text_content = result[0]
                    if hasattr(text_content, 'text'):
                        try:
                            json_data = json.loads(text_content.text)
                            
                            save_status = json_data.get('save_status', {})
                            if save_status.get('status') == 'success':
                                logger.info(f"Successfully scraped LinkedIn profile for {speaker_name}")
                                return True
                            else:
                                logger.error(f"Failed to scrape {speaker_name}: {save_status.get('message', 'Unknown error')}")
                                return False
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON response for {speaker_name}: {e}")
                            return False
                    else:
                        logger.error(f"TextContent missing 'text' attribute for {speaker_name}")
                        return False
                else:
                    logger.error(f"Unexpected response format for {speaker_name}: {type(result)}")
                    return False
            else:
                logger.error(f"Invalid response from MCP server for {speaker_name}")
                return False
                
        finally:
            await client.close_all_sessions()
            
    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile for {speaker_name}: {e}")
        return False


def load_linkedin_profiles_by_slug(
    profiles_dir: str, speakers: List[Dict]
) -> Dict[str, Dict]:
    """Load LinkedIn profiles from disk by slug for speakers with LinkedIn URLs"""
    profiles = {}
    for speaker in speakers:
        linkedin_url = speaker.get("linkedin_url", "").strip()
        if not linkedin_url:
            continue
            
        slug = linkedin_slug(linkedin_url)
        event_name = speaker.get("event", "")
        sanitized_event = sanitize_event_name(event_name)
        
        json_path = os.path.join(profiles_dir, sanitized_event, f"{slug}.json")
        
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                    profiles[speaker["name"]] = profile
                    logger.info(f"Loaded LinkedIn profile for {speaker['name']}")
            except Exception as e:
                logger.warning(
                    f"Failed to load profile for {speaker['name']} from {json_path}: {e}"
                )
        else:
            logger.info(f"Profile JSON not found for {speaker['name']} (slug: {slug})")
            
    logger.info(f"Loaded {len(profiles)} LinkedIn profiles from {profiles_dir}")
    return profiles


async def ensure_linkedin_profiles(speakers: List[Dict], profiles_dir: str) -> Dict[str, Dict]:
    """Ensure all speakers have LinkedIn profiles, scraping missing ones"""
    profiles = {}
    
    for speaker in speakers:
        name = speaker.get("name", "")
        linkedin_url = speaker.get("linkedin_url", "").strip()
        event_name = speaker.get("event", "")
        
        if not linkedin_url:
            logger.warning(f"No LinkedIn URL for {name}, skipping profile loading")
            continue
            
        slug = linkedin_slug(linkedin_url)
        sanitized_event = sanitize_event_name(event_name)
        
        json_path = os.path.join(profiles_dir, sanitized_event, f"{slug}.json")
        
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                    profiles[name] = profile
                    logger.info(f"Profile already exists for {name}")
            except Exception as e:
                logger.warning(f"Failed to load existing profile for {name}: {e}")
                logger.info(f"Attempting to re-scrape profile for {name}")
                success = await scrape_missing_linkedin_profile(linkedin_url, event_name, name)
                if success:
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            profile = json.load(f)
                            profiles[name] = profile
                    except Exception as load_e:
                        logger.error(f"Failed to load newly scraped profile for {name}: {load_e}")

        else:
            logger.info(f"Profile missing for {name}, scraping now...")
            success = await scrape_missing_linkedin_profile(linkedin_url, event_name, name)
            if success:
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        profile = json.load(f)
                        profiles[name] = profile
                        logger.info(f"Successfully loaded newly scraped profile for {name}")
                except Exception as load_e:
                    logger.error(f"Failed to load newly scraped profile for {name}: {load_e}")
            else:
                logger.error(f"Failed to scrape profile for {name}")
    
    return profiles


def merge_input_output_files(input_csv: str, output_csv: str, merged_csv: str):
    """Merge input CSV with output CSV to create a single overview file using pandas"""
    try:
        import pandas as pd
        
        input_df = pd.read_csv(input_csv, delimiter=';', on_bad_lines='warn', engine='python')
        
        output_df = pd.read_csv(output_csv, delimiter=';', on_bad_lines='warn', engine='python')
        
        input_df['name'] = input_df['name'].str.strip()
        output_df['name'] = output_df['name'].str.strip()
        
        merged_df = pd.merge(
            input_df, 
            output_df, 
            on='name', 
            how='left'
        )
        
        merged_df.drop(columns=['name'], inplace=True)
        
        merged_df.to_csv(merged_csv, sep=';', index=False)
        print(merged_df.head())
        
        logger.info(f"Merged {len(merged_df)} records to {merged_csv}")
        return True
        
    except Exception as e:
        logger.error(f"Error merging files: {e}")
        return False


def create_batch_requests(speakers: List[Dict], profiles: Dict[str, Dict] = None) -> List[Dict]:
    """Create batch requests for Claude API"""
    batch_requests = []

    system_prompt = [
        {
            "type": "text",
            "text": """You are creating humble, unassuming LinkedIn connection requests for people who attended Groundswell Festival who have been pre-selected for relevance to Muryo.

BUSINESS CONTEXT - Muryo:
- Mission: AI copilot that de-risks the transition to sustainable crop production by bridging the science/implementation gap — turning research into actionable, farm-specific guidance that balances economic viability with environmental stewardship.
- Approach: Humble, learning-focused, research-backed
- Stage: Early validation - genuinely seeking to understand market needs
- Tone: Curious researcher also attended the event, not salesy entrepreneur

GROUNDSWELL FESTIVAL CONTEXT:
- You have both attended the same event (natural connection point)
- Many are speakers/experts (acknowledge their expertise humbly)
- Referencing specific sessions they're involved in shows genuine interest
- Much more natural than cold LinkedIn outreach

MESSAGE REQUIREMENTS:
- Under 280 characters (LinkedIn initial connection request limit)
- Humble tone: "exploring," "learning about," "interested in understanding"
- Unassuming: "would appreciate," "if you're open to," "briefly"
- Curious: "noticed," "intrigued by," "looking forward to"
- Respectful: Acknowledge their expertise without being overly deferential
- PRIORITIZE mentioning you're both attending Groundswell
- Reference specific sessions when relevant
- No sales language whatsoever

MESSAGING APPROACH:
Focus on shared event attendance first, then specific interests:
- "I attended Groundswell and noticed you're involved in..."

PERSONALIZATION HIERARCHY (use BEST available):
1. Specific session they're speaking at/involved in + relevant background detail
2. Session topic they're attending + their expertise area
3. Their speaker bio/profile expertise + humble learning angle
4. LinkedIn career details + Groundswell connection

AVOID:
- Generic "looking forward to connecting at the event"
- Any mention of Muryo's product/features
- Sales language ("solution," "platform," "offering")
- Overly formal or overly casual tone
- Vague references without specifics
- Making it about you rather than them
- Having an over optimistic tone (incl. ex: "is exactly the expertise I'm exploring in..")

RETURN ONLY THE FOLLOWING JSON:
{
    "name": Name, as provided
    "message": The connection request message,
    "send_recommendation": Yes/No - whether message quality is good enough to send
}

High confidence = specific session reference + relevant background detail + natural Groundswell connection
Medium confidence = good session/bio reference + Groundswell mention
Low confidence = generic or weak personalization""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for speaker in speakers:
        name = speaker.get("name", "")
        bio = speaker.get("bio", "")
        detailed_profile = speaker.get("detailed_profile", "")
        selected_sessions = speaker.get("selected_sessions", "")
        
        linkedin_profile = profiles.get(name, {}) if profiles else {}
        
        current_roles = []
        if linkedin_profile.get("experiences"):
            for exp in linkedin_profile.get("experiences", [])[:3]:
                role_info = (
                    f"{exp.get('position_title', '')} at {exp.get('company', '')}"
                )
                if exp.get("description"):
                    desc = exp.get("description", "")
                    role_info += f" - {desc}"
                current_roles.append(role_info)

        educations = linkedin_profile.get("educations")
        if educations and isinstance(educations, list) and len(educations) > 0:
            institution = educations[0].get("institution") or ""
            degree = educations[0].get("degree") or ""
            education_str = f"{institution} - {degree}".strip(" -")
            if not education_str:
                education_str = "Not available"
        else:
            education_str = "Not available"

        user_prompt = f"""Please generate a humble LinkedIn connection request for this person that attended Groundswell Festival.

SPEAKER INFORMATION:
Name: {name}
Bio: {bio}
Detailed Profile: {detailed_profile}
Selected Sessions: {selected_sessions if selected_sessions else "Not specified"}

LINKEDIN PROFILE DATA:
Name: {linkedin_profile.get("name", "")}
About Section: {linkedin_profile.get("about", "") if linkedin_profile.get("about") else "Not available"}
Professional Roles:
{chr(10).join(current_roles) if current_roles else "Not available"}
Education: {education_str}

INSTRUCTIONS:
1. Start by mentioning you came across their work via Groundswell. Avoid saying you participated at their session.
2. Reference the MOST specific and relevant detail from their bio, profile, selected sessions, or LinkedIn data
3. Generate a humble, curious connection request under 280 characters
4. Focus on genuine interest in learning from their expertise
5. Maintain professional but approachable tone
6. NO sales language - just authentic curiosity

EXAMPLE APPROACHES:
- "Hi Abby, came across your work at Vidacycle during Groundswell this year and it's very relevant to challenges I'm researching in the transition to sustainable production. Would love to connect!"
- "Hi Joseph, I saw your NIAB stand tour listed at Groundswell on regen-ag science. As someone exploring the business case for regenerative practices, I'd value connecting with researchers who understand both the science and practical implementation challenges."

Generate a connection request that feels naturally crafted around your shared event attendance."""

        clean_name = clean_string(name)[:30]
        custom_id = f"groundswell_{clean_name}"

        batch_request = {
            "custom_id": custom_id,
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        }
        batch_requests.append(batch_request)

    return batch_requests


async def main():
    parser = argparse.ArgumentParser(
        description="Generate LinkedIn outreach messages for Groundswell speakers using CSV input with LinkedIn URLs"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="CSV file with speakers data (must have 'linkedin' column with LinkedIn URLs)",
    )
    parser.add_argument(
        "--linkedin_profiles_dir",
        default=os.path.expandvars("$HOME/linkedin_data/"),
        help="Base directory for LinkedIn profiles (default: $HOME/linkedin_data/)",
    )
    parser.add_argument(
        "--output",
        default="data/groundswell_remaining_outreach_messages.csv",
        help="Output CSV file",
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set.")
        logger.info("Please set the environment variable and try again.")
        sys.exit(1)
    client = Anthropic(api_key=api_key)

    required_env_vars = ["LINKEDIN_EMAIL", "LINKEDIN_PASSWORD", "CHROMEDRIVER"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("These are needed for LinkedIn profile scraping.")
        sys.exit(1)

    logger.info("Loading speakers from CSV...")
    speakers = load_speakers_from_csv(args.input)

    '''
    logger.info("Checking and scraping LinkedIn profiles...")
    profiles = await ensure_linkedin_profiles(speakers, args.linkedin_profiles_dir)

    logger.info(f"Creating batch requests for {len(speakers)} speakers...")

    batch_requests = create_batch_requests(speakers, profiles)

    logger.info("Submitting batch job...")
    batch_id = create_batch_job(client, batch_requests)
    results_url = poll_for_batch_completion(
        client, batch_id, poll_interval=args.poll_interval
    )

    json_filename = args.output.replace('.csv', '.json')
    
    download_results_file(results_url, json_filename, api_key)
    
    json_to_csv(json_filename, args.output)
    '''
    
    merged_filename = args.output.replace('.csv', '_merged.csv')
    if merge_input_output_files(args.input, args.output, merged_filename):
        logger.info(f"Merged overview saved to {merged_filename}")
    else:
        logger.warning("Failed to create merged overview file")
    
    logger.info(f"All done! CSV output saved to {args.output}")
    logger.info(f"Merged overview saved to {merged_filename}")


if __name__ == "__main__":
    asyncio.run(main())
