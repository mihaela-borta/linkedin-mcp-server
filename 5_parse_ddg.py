import csv
import os
import logging
import argparse
from anthropic import Anthropic
from typing import Dict, List
from utils import (
    jsonl_to_csv,
    clean_string,
    create_batch_job,
    poll_for_batch_completion,
    download_results_file,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("parse_ddg")


def load_input_data(filename: str) -> List[Dict]:
    """Load the CSV data with search results"""
    contacts = []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            # Lowercase all keys for consistency
            contacts.append({k.lower(): v for k, v in row.items()})
    return contacts


def create_batch_requests(contacts: List[Dict]) -> List[Dict]:
    """Create batch requests for Claude API"""
    batch_requests = []

    system_prompt = [
        {
            "type": "text",
            "text": """You are an expert at extracting and organizing professional information from web search results. Your task is to analyze search results for individuals and extract structured professional data.

Extract the following information, respecting the guidance and format (including field order):
- company: Current employer
- title: Job position
- name: Name as provided
- email: Professional email address
- phone: Primary phone number
- linkedin: Personal profile URL
    Rules for extraction:
        - ensure the link is for the person we are analyzing, and not that of a company (the name in the linkedin URL should match to some extent to the name of the person)
        - in case no personal link is found, extract from Linkedin post URLs: https://www.linkedin.com/posts/[username]_ becomes https://www.linkedin.com/in/[username]). Same logic applies to UK LinkdeIn links
        - add the https:// to the link if it is missing
- linkedin_slug: slug from the LinkedIn personal profile link if one was found
- location: City/region
- industry: Business sector
- brief_profile: Brief relevant details for engagement (max 100 words)
- detailed_profile: Comprehensive background including experience, expertise, achievements, education, personal business ventures, and professional philosophy if available (200-300 words)
- media_links: URLs to interviews, articles, videos, podcasts, or other media appearances featuring the person (pipe-separated if multiple)
- professional_links: URLs to company profiles, bio pages, professional websites, or other business-related pages (pipe-separated if multiple)

Return ONLY a JSON object with these exact field names. If information is not available, use empty string.

LinkedIn profile data and search results will be provided in the user message.""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for i, contact in enumerate(contacts):
        user_prompt = f"""Please extract professional information for this person:

organization: {contact.get("organization", "")}
job_title: {contact.get("job_title", "")}
name: {contact.get("name", "")}

search results:
{contact.get("ddg_search", "")}

Please analyze these search results and extract the requested information in JSON format."""

        name = clean_string(contact.get("name", ""))[:30]
        org = clean_string(contact.get("organization", ""))[:30]
        custom_id = f"{name}_{org}"

        batch_request = {
            "custom_id": custom_id,
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        }
        batch_requests.append(batch_request)

    return batch_requests


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Parse DuckDuckGo search results using Claude and download results automatically."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/groundswellag_speaker_ddg_results.csv",
        help="Input CSV file with DuckDuckGo search results (default: data/groundswellag_speaker_ddg_results.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_parsed_ddg_results.csv",
        help="Output CSV file for parsed results (default: data/groundswellag_speakers_parsed_ddg_results.csv)",
    )
    parser.add_argument(
        "--jsonl",
        type=str,
        default="data/groundswellag_speakers_parsed_ddg_results.jsonl",
        help="Intermediate JSONL file to store batch results (default: data/groundswellag_speakers_parsed_ddg_results.jsonl)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    args = parser.parse_args()

    # Initialize Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)

    # Load input data
    logger.info("Loading input data...")
    contacts = load_input_data(args.input)[:1]
    logger.info(f"Loaded {len(contacts)} contacts")

    # Create batch requests
    logger.info("Creating batch requests...")
    batch_requests = create_batch_requests(contacts)

    # Submit batch job
    logger.info("Submitting batch job...")
    batch_id = create_batch_job(client, batch_requests)
    results_url = poll_for_batch_completion(
        client, batch_id, poll_interval=args.poll_interval
    )
    download_results_file(results_url, args.jsonl, api_key)

    # Convert JSONL to CSV
    logger.info("Converting JSONL results to CSV...")
    jsonl_to_csv(args.jsonl, args.output)
    logger.info(f"All done! CSV output saved to {args.output}")


if __name__ == "__main__":
    main()
