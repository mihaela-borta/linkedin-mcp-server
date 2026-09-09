#!/usr/bin/env python3
"""
Extract name, LinkedIn URL, and company from JSON files in LinkedIn data directory.
Outputs to a semicolon-separated CSV file.
"""

import json
import os
import csv
from pathlib import Path
from typing import Dict, Optional


def extract_profile_data(json_file_path: Path) -> Optional[Dict[str, str]]:
    """Extract name, LinkedIn URL, and company from a JSON file."""
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract the required fields
        name = data.get("name", "")
        linkedin_url = data.get("linkedin_url", "")
        company = data.get("company", "")

        # If any required field is missing, return None
        if not name or not linkedin_url:
            print(f"Warning: Missing required fields in {json_file_path}")
            return None

        return {"name": name, "linkedin_url": linkedin_url, "company": company}

    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error processing {json_file_path}: {e}")
        return None


def main():
    # Get LinkedIn data directory from environment or use default
    linkedin_data_dir = os.path.expanduser(
        os.getenv("LINKEDIN_DATA_DIR", "~/linkedin_data")
    )

    # Look for event subdirectories
    linkedin_data_path = Path(linkedin_data_dir)
    if not linkedin_data_path.exists():
        print(f"LinkedIn data directory not found: {linkedin_data_path}")
        return

    # Find all JSON files in subdirectories
    json_files = []
    for event_dir in linkedin_data_path.iterdir():
        if event_dir.is_dir():
            json_files.extend(event_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {linkedin_data_path}")
        return

    print(f"Found {len(json_files)} JSON files to process")

    # Extract data from all files
    profiles = []
    for json_file in json_files:
        profile_data = extract_profile_data(json_file)
        if profile_data:
            profiles.append(profile_data)

    print(f"Successfully extracted data from {len(profiles)} profiles")

    # Create output directory if it doesn't exist
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    # Write to CSV file
    output_file = output_dir / "linkedin_profiles_extracted.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["name", "linkedin_url", "company"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")

        writer.writeheader()
        for profile in profiles:
            writer.writerow(profile)

    print(f"Data saved to {output_file}")
    print(f"Total profiles extracted: {len(profiles)}")


if __name__ == "__main__":
    main()
