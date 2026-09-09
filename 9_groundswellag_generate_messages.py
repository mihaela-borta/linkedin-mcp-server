#!/usr/bin/env python3
"""
Generate LinkedIn outreach messages for scored Groundswell speakers using LinkedIn profiles and Claude Batches API.
"""

import json
import os
import logging
import argparse
from anthropic import Anthropic
from typing import Dict, List
import pandas as pd
from utils import (
    clean_string,
    create_batch_job,
    poll_for_batch_completion,
    download_results_file,
    jsonl_to_csv,
)
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("message_generator")


def load_scored_speakers(csv_file: str) -> List[Dict]:
    """Load the scored speakers CSV with lowercase column names"""
    speakers = []
    try:
        df = pd.read_csv(csv_file, sep=";")
        df.columns = [col.lower() for col in df.columns]
        logger.info(f"Loaded {len(df)} scored speakers from {csv_file}")
        for _, row in df.head(1).iterrows():
            speaker = {
                col: row[col] if pd.notna(row[col]) else "" for col in df.columns
            }
            speakers.append(speaker)
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        raise
    return speakers


def load_linkedin_profiles_by_slug(
    profiles_dir: str, speakers: List[Dict]
) -> Dict[str, Dict]:
    """Load LinkedIn profiles from disk by slug for speakers with non-empty linkedin_slug."""
    profiles = {}
    for speaker in speakers:
        slug = speaker.get("linkedin_slug", "").strip()
        if slug:
            json_path = os.path.join(profiles_dir, f"{slug}.json")
            if os.path.isfile(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        profile = json.load(f)
                        profiles[speaker["name"]] = profile
                except Exception as e:
                    logger.warning(
                        f"Failed to load profile for {speaker['name']} from {json_path}: {e}"
                    )
            else:
                logger.info(
                    f"Profile JSON not found for slug {slug} ({speaker['name']})"
                )
    logger.info(f"Loaded {len(profiles)} LinkedIn profiles by slug from {profiles_dir}")
    return profiles


def create_batch_requests(
    speakers: List[Dict], profiles: Dict[str, Dict]
) -> List[Dict]:
    """Create batch requests for Claude API"""
    batch_requests = []

    system_prompt = [
        {
            "type": "text",
            "text": """You are creating humble, unassuming LinkedIn connection requests for people attending Groundswell Festival who have been pre-scored for relevance to Muryo.

BUSINESS CONTEXT - Muryo:
- Mission: AI copilot that de-risks the transition to sustainable crop production by bridging the science/implementation gap — turning research into actionable, farm-specific guidance that balances economic viability with environmental stewardship.
- Approach: Humble, learning-focused, research-backed
- Stage: Early validation - genuinely seeking to understand market needs
- Tone: Curious researcher also attending the conference, not salesy entrepreneur

GROUNDSWELL FESTIVAL CONTEXT:
- You're both attending the same conference (natural connection point)
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
Focus on shared conference attendance first, then specific interests:
- "I'll also be at Groundswell and noticed..."
- "Looking forward to Groundswell and saw you're involved in..."
- "I'll be attending Groundswell too and was intrigued by..."

PERSONALIZATION HIERARCHY (use BEST available):
1. Specific session they're speaking at/involved in + relevant background detail
2. Session topic they're attending + their expertise area
3. Their speaker bio/profile expertise + humble learning angle
4. LinkedIn career details + Groundswell connection

TONE EXAMPLES:
- "I'll also be at Groundswell and noticed you're speaking about [topic]"
- "Looking forward to Groundswell and saw your session on [specific topic]"
- "I'll be at Groundswell too and was intrigued by your work with [company/research]"
- "Attending Groundswell as well and excited to hear your perspective on [topic]"

AVOID:
- Generic "looking forward to connecting at the event"
- Any mention of Muryo's product/features
- Sales language ("solution," "platform," "offering")
- Overly formal or overly casual tone
- Vague references without specifics
- Making it about you rather than them

RETURN ONLY THE FOLLOWING JSON:
{
    "name": Name, as provided
    "message": The connection request message,
    "personalization_source": What specific element was used (session, bio, LinkedIn detail),
    "confidence_level": High/Medium/Low based on personalization quality,
    "send_recommendation": Yes/No - whether message quality is good enough to send
}

High confidence = specific session reference + relevant background detail + natural Groundswell connection
Medium confidence = good session/bio reference + Groundswell mention
Low confidence = generic or weak personalization""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for i, speaker in enumerate(speakers):
        name = speaker.get("name", "")

        # Try to find matching LinkedIn profile
        linkedin_profile = profiles.get(name, {})

        # Extract key info from LinkedIn experiences
        current_roles = []
        if linkedin_profile.get("experiences"):
            for exp in linkedin_profile.get("experiences", [])[:2]:  # Top 2 most recent
                role_info = (
                    f"{exp.get('position_title', '')} at {exp.get('company', '')}"
                )
                if exp.get("description"):
                    desc = exp.get("description", "")[:150]
                    role_info += f" - {desc}"
                current_roles.append(role_info)

        # Safely extract education string
        educations = linkedin_profile.get("educations")
        if educations and isinstance(educations, list) and len(educations) > 0:
            institution = educations[0].get("institution") or ""
            degree = educations[0].get("degree") or ""
            education_str = f"{institution} - {degree}".strip(" -")
            if not education_str:
                education_str = "Not available"
        else:
            education_str = "Not available"

        user_prompt = f"""Please generate a humble LinkedIn connection request for this person attending Groundswell Festival. The message should take into account the outreach timing.

SCORING DATA:
Name: {speaker.get("name", "")}
Outreach Timing: {speaker.get("name", "")}
Priority Score: {speaker.get("outreach_timing", "")}
Customer Category: {speaker.get("customer_category", "")}
Network Level: {speaker.get("network_level", "")}
Key Value Proposition: {speaker.get("key_value_proposition", "")}
Approach Type: {speaker.get("approach_type", "")}
Critical Notes: {speaker.get("critical_notes", "")}

GROUNDSWELL FESTIVAL CONTEXT:
Speaker Bio: {speaker.get("speaker_bio", "")}
Selected Sessions: {speaker.get("selected_session", "")}
All Sessions: {speaker.get("session_names", "")}
All Session Descriptions: {speaker.get("session_descriptions", "")}

BACKGROUND PROFILE DATA:
Detailed Profile: {speaker.get("detailed_profile", "")}

LINKEDIN PROFILE DATA:
Name: {linkedin_profile.get("name", "")}
About Section: {linkedin_profile.get("about", "") if linkedin_profile.get("about") else ""}
Current Professional Roles:
{chr(10).join(current_roles) if current_roles else "Not available"}
Education: {education_str}

INSTRUCTIONS:
1. Start by mentioning you're both attending Groundswell (shared context)
2. Reference the MOST specific and relevant detail (prioritize sessions they're involved in and are the most particularly relevant for our validation and their bio)
3. Generate a humble, curious connection request under 280 characters
4. Focus on genuine interest in learning from their expertise
5. Maintain professional but approachable tone
6. NO sales language - just authentic curiosity

EXAMPLE APPROACHES:
- "Hi [firstname], I'll also be at Groundswell and noticed your session on [specific topic]"
- "Hi [firstname], Looking forward to Groundswell and saw you're speaking about [topic]"
- "Hi [firstname], I'll be attending Groundswell too and was intrigued by your work with [specific area]"
- Hi [firstname], good to see you at Groundswell! Enjoyed the [brief reference to the most relevant selected session] session you spoke at.

Generate a connection request that feels naturally crafted around your shared conference attendance.
Output the following info, in the format specified:
- name: Name, as provided


"""

        # Use imported clean_string for custom_id
        name = clean_string(speaker.get("name", ""))[:30]
        org = clean_string(speaker.get("company", ""))[:30]
        custom_id = f"{name}_{org}"

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


def main():
    parser = argparse.ArgumentParser(
        description="Generate LinkedIn outreach messages for scored Groundswell speakers using batches"
    )
    parser.add_argument(
        "--speakers",
        default="data/groundswellag_speakers_from_handpicked_w_scores_1.csv",
        help="CSV file with scored speakers",
    )
    parser.add_argument(
        "--profiles",
        default=os.path.expandvars("$HOME/linkedin_data/groundswellag/"),
        help="Folder with LinkedIn profiles (by slug)",
    )
    parser.add_argument(
        "--output",
        default="data/groundswellag_outreach_messages_1.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--limit", type=int, default=25, help="Limit number of messages to generate"
    )
    parser.add_argument(
        "--test-person",
        default="",
        help="Test with specific person (e.g., 'Abby Rose')",
    )
    parser.add_argument(
        "--jsonl",
        default="data/groundswellag_outreach_messages.jsonl",
        help="Intermediate JSONL file to store batch results (default: data/groundswellag_outreach_messages.jsonl)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    args = parser.parse_args()

    # Initialize Anthropic client and check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set.")
        logger.info("Please set the environment variable and try again.")
        sys.exit(1)
    client = Anthropic(api_key=api_key)

    # Load data
    logger.info("Loading scored speakers...")
    speakers = load_scored_speakers(args.speakers)

    # Filter for test person if specified
    if args.test_person:
        speakers = [
            c for c in speakers if args.test_person.lower() in c.get("name", "").lower()
        ]
        logger.info(
            f"Filtered to test person: {args.test_person} ({len(speakers)} matches)"
        )

    logger.info("Loading LinkedIn profiles by slug...")
    profiles = load_linkedin_profiles_by_slug(args.profiles, speakers)

    # Filter to highest priority speakers.TODO: the profiles should be sorted similarly
    # speakers = sorted(speakers, key=lambda x: float(x.get('priority_score', 0)), #reverse=True)
    # speakers = speakers[:args.limit]

    logger.info(f"Creating batch requests for {len(speakers)} speakers...")

    # Create batch requests
    batch_requests = create_batch_requests(speakers, profiles)

    logger.info("Submitting batch job...")
    batch_id = create_batch_job(client, batch_requests)
    results_url = poll_for_batch_completion(
        client, batch_id, poll_interval=args.poll_interval
    )

    download_results_file(results_url, args.jsonl, api_key)

    jsonl_to_csv(args.jsonl, args.output)
    logger.info(f"All done! CSV output saved to {args.output}")


if __name__ == "__main__":
    main()
