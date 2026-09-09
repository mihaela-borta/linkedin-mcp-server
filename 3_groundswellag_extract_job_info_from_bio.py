#!/usr/bin/env python3
"""
Extract job titles, organizations, and search keywords from speaker bios using Claude API.
Takes a CSV with speaker_bio column and outputs organization, job_title, name, and search_keywords.
Enhanced for better LinkedIn profile searches.
"""

import os
import logging
import argparse
from anthropic import Anthropic
from typing import Dict, List
from utils import (
    jsonl_to_csv,
    create_batch_job,
    poll_for_batch_completion,
    download_results_file,
    clean_string,
)
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("extract_job_info")


def load_input_data(filename: str) -> List[Dict]:
    """Load the CSV data with speaker bios"""
    speakers = []
    try:
        df = pd.read_csv(filename)
        logger.info(f"Loaded {len(df)} speaker records from {filename}")

        # Check available columns and determine which ones to use
        available_columns = df.columns.tolist()
        logger.info(f"Available columns: {available_columns}")

        # Determine name column
        name_column = None
        if "speaker_name" in available_columns:
            name_column = "speaker_name"
        elif "name" in available_columns:
            name_column = "name"
        else:
            raise ValueError("No name column found. Expected 'speaker_name' or 'name'")

        # Determine bio column
        bio_column = None
        if "speaker_bio" in available_columns:
            bio_column = "speaker_bio"
        elif "bio" in available_columns:
            bio_column = "bio"
        else:
            raise ValueError("No bio column found. Expected 'speaker_bio' or 'bio'")

        logger.info(f"Using name column: {name_column}")
        logger.info(f"Using bio column: {bio_column}")

        # Convert to list of dictionaries
        for _, row in df.iterrows():
            speaker = {
                "name": row[name_column] if pd.notna(row[name_column]) else "",
                "bio": row[bio_column] if pd.notna(row[bio_column]) else "",
            }
            speakers.append(speaker)

    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        raise

    return speakers


def create_batch_requests(speakers: List[Dict]) -> List[Dict]:
    """Create batch requests for Claude API"""
    batch_requests = []

    system_prompt = [
        {
            "type": "text",
            "text": """You are an expert at extracting professional information from speaker biographies for LinkedIn profile searches. Your task is to analyze speaker bios and extract structured professional data.

Extract the following information and format as specified:
- organization: Current employer or organization the person works for/represents
- job_title: Current job position or role (be specific and capture unconventional titles)
- name: name of the person as provided
- search_keywords: 3-5 distinctive keywords/phrases that would help find their LinkedIn profile (pipe-separated)

Guidelines for extraction:
1. Look for current roles and organizations mentioned in the bio
2. Job titles can be unconventional - capture the actual title used (e.g., "Deep Ecologist and co-founder", "first-generation mixed farmer", "Head of Natural Capital")
3. If someone is self-employed or runs their own business, use the business name as organization
4. If multiple organizations are mentioned, prioritize the current/primary one
5. If no clear organization is found, use empty string
6. For job titles, be specific and include qualifiers (e.g., "Organic arable farmer" not just "farmer")

For search_keywords, include:
- Specific company names, projects, or initiatives they're associated with
- Unique qualifications, awards, or recognitions
- Geographic locations (cities, regions, countries)
- Industry-specific terms or specializations
- Notable publications, books, or research areas
- Professional certifications or memberships
- Avoid generic terms that appear in many profiles

Examples of good search_keywords:
- "Soil Association trustee|Wiltshire|organic farming|regenerative agriculture"
- "Nuffield Farming Scholar|Pasture for Life|grass-fed beef|Devon"
- "Wildfarmed|regenerative wheat|soil health|UK agriculture"

Return ONLY a JSON object with these exact field names. If information is not available, use empty string.

Speaker bio will be provided in the user message.""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for i, speaker in enumerate(speakers):
        user_prompt = f"""Please extract professional information for this person:

Name: {speaker["name"]}
Bio: {speaker["bio"]}

Please analyze this speaker bio and extract the requested information in JSON format."""

        name = clean_string(speaker["name"])[:30]
        custom_id = f"speaker_{name}_{i}"

        batch_request = {
            "custom_id": custom_id,
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        }
        batch_requests.append(batch_request)

    return batch_requests


def main():
    parser = argparse.ArgumentParser(
        description="Extract job titles, organizations, and search keywords from speaker bios using Claude. Fully automated batch workflow."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_sessions.csv",
        help="Input CSV file with speaker bios (default: data/groundswellag_speakers_from_handpicked_sessions.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speaker_search_terms.csv",
        help="Output CSV file for extracted job info (default: data/groundswellag_speaker_search_terms.csv)",
    )
    parser.add_argument(
        "--jsonl",
        type=str,
        default="data/groundswellag_speaker_search_terms.jsonl",
        help="Intermediate JSONL file to store batch results (default: data/groundswellag_speaker_search_terms.jsonl)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60)",
    )
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)

    # Load input data
    logger.info("Loading input data...")
    speakers = load_input_data(args.input)
    logger.info(f"Loaded {len(speakers)} speakers")

    # Create batch requests
    logger.info("Creating batch requests...")
    batch_requests = create_batch_requests(speakers)

    # Submit batch job
    logger.info("Submitting batch job...")
    batch_id = create_batch_job(client, batch_requests)

    # Poll for completion and get results_url
    results_url = poll_for_batch_completion(
        client, batch_id, poll_interval=args.poll_interval
    )

    # Download the results file
    download_results_file(results_url, args.jsonl, api_key)

    # Convert JSONL to CSV
    logger.info("Converting JSONL results to CSV...")
    jsonl_to_csv(args.jsonl, args.output)
    logger.info(f"All done! CSV output saved to {args.output}")


if __name__ == "__main__":
    main()
