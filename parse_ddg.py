import csv
import json
import os
import logging
import argparse
from anthropic import Anthropic
from typing import Dict, List
import time

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
            contacts.append(row)
    return contacts


def create_batch_requests(contacts: List[Dict]) -> List[Dict]:
    """Create batch requests for Claude API"""
    batch_requests = []

    system_prompt = [
        {
            "type": "text",
            "text": """You are an expert at extracting and organizing professional information from web search results. Your task is to analyze search results for individuals and extract structured professional data.

Extract the following information and format as specified:
- Company: Current employer
- Title: Job position
- Name: Full name
- Email: Professional email address
- Phone: Primary phone number
- LinkedIn: Personal profile URL (extract from post URLs: linkedin.com/posts/[username]_ becomes linkedin.com/in/[username])
- Location: City/region
- Industry: Business sector
- Brief_Profile: Brief relevant details for engagement (max 100 words)
- Detailed_Profile: Comprehensive background including experience, expertise, achievements, education, personal business ventures, and professional philosophy if available (200-300 words)
- Media_Links: URLs to interviews, articles, videos, podcasts, or other media appearances featuring the person (pipe-separated if multiple)
- Professional_Links: URLs to company profiles, bio pages, professional websites, or other business-related pages (pipe-separated if multiple)

Return ONLY a JSON object with these exact field names. If information is not available, use empty string.

LinkedIn profile data and search results will be provided in the user message.""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for i, contact in enumerate(contacts):
        user_prompt = f"""Please extract professional information for this person:

Organization: {contact["organization"]}
Job Title: {contact["job_title"]}
Name: {contact["name"]}
Event: {contact["event"]}

Search Results:
{contact["ddg_search"]}

Please analyze these search results and extract the requested information in JSON format."""

        # Create a custom_id that matches the pattern ^[a-zA-Z0-9_-]{1,64}$
        def clean_string(s: str) -> str:
            # Handle Danish characters first
            s = s.replace("Ø", "Oe").replace("ø", "oe")
            s = s.replace("Æ", "Ae").replace("æ", "ae")
            s = s.replace("Å", "Aa").replace("å", "aa")
            # Convert to ASCII, replacing any remaining non-ASCII chars
            s = s.encode("ascii", "replace").decode("ascii")
            # Replace spaces with nothing and keep only alphanumeric
            s = "".join(c for c in s if c.isalnum())
            return s or "unknown"

        name = clean_string(contact["name"])[:30]
        org = clean_string(contact["organization"])[:30]
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


def create_batch_job(client: Anthropic, requests: List[Dict]) -> str:
    """Create and submit batch job"""
    batch = client.messages.batches.create(requests=requests)
    logger.info(f"Batch job created with ID: {batch.id}")
    return batch.id


def check_batch_status(client: Anthropic, batch_id: str) -> bool:
    """Check the status of a batch job"""
    batch = client.messages.batches.retrieve(batch_id)
    logger.info(f"Batch status: {batch.processing_status}")
    logger.info(
        f"Full batch response: {batch}"
    )  # Debug log to see the actual structure

    # Check if all requests are either succeeded or failed
    total_requests = (
        batch.request_counts.processing
        + batch.request_counts.succeeded
        + batch.request_counts.errored
        + batch.request_counts.canceled
        + batch.request_counts.expired
    )
    completed_requests = (
        batch.request_counts.succeeded
        + batch.request_counts.errored
        + batch.request_counts.canceled
        + batch.request_counts.expired
    )

    if completed_requests >= total_requests:
        logger.info(
            f"Batch processing completed: {completed_requests}/{total_requests} requests done"
        )
        return True
    elif batch.processing_status == "failed":
        logger.error("Batch failed")
        return True  # Return True to stop checking
    else:
        logger.info(
            f"Batch in progress: {completed_requests}/{total_requests} requests completed"
        )
        # If we're still processing, wait a bit longer
        time.sleep(60)  # Wait 60 seconds between checks
        return False


def process_batch_results(client: Anthropic, batch_id: str, output_csv: str):
    """Process batch results and save to CSV"""
    # Wait a bit before trying to get results
    time.sleep(10)

    try:
        batch = client.messages.batches.retrieve(batch_id)
        results = []

        for result in batch.results:
            if result.status == "succeeded":
                try:
                    content = result.response.content[0].text
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1

                    if json_start != -1 and json_end != -1:
                        extracted_data = json.loads(content[json_start:json_end])
                        results.append(extracted_data)
                        logger.info(f"Successfully processed {result.custom_id}")
                    else:
                        logger.warning(
                            f"Could not extract JSON from response for {result.custom_id}"
                        )
                except Exception as e:
                    logger.error(f"Error processing {result.custom_id}: {e}")
            else:
                logger.error(f"Request {result.custom_id} failed: {result.error}")

        # Write to CSV
        if results:
            fieldnames = [
                "Company",
                "Name",
                "Title",
                "Email",
                "Phone",
                "LinkedIn",
                "Location",
                "Industry",
                "Brief_Profile",
                "Detailed_Profile",
                "Media_Links",
                "Professional_Links",
            ]

            with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                writer.writerows(results)

            logger.info(f"CSV output saved to {output_csv}")
            logger.info(f"Processed {len(results)} records")
        else:
            logger.warning("No results were processed successfully")
    except Exception as e:
        logger.error(f"Error retrieving batch results: {e}")
        # If we get a "no available results" error, wait and try again
        if "no available results" in str(e).lower():
            logger.info("Waiting for results to become available...")
            time.sleep(30)  # Wait 30 seconds
            return process_batch_results(client, batch_id, output_csv)  # Retry
        raise  # Re-raise other exceptions


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Parse DuckDuckGo search results using Claude"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/ddg_results_folkemødet.csv",
        help="Input CSV file with DuckDuckGo search results (default: data/ddg_results_folkemødet.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/parsed_ddg_results_folkemødet.csv",
        help="Output CSV file for parsed results (default: data/parsed_ddg_results_folkemødet.csv)",
    )
    args = parser.parse_args()

    # Initialize Anthropic client
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Load input data
    logger.info("Loading input data...")
    contacts = load_input_data(args.input)
    logger.info(f"Loaded {len(contacts)} contacts")

    # Create batch requests
    logger.info("Creating batch requests...")
    batch_requests = create_batch_requests(contacts)

    # Submit batch job
    logger.info("Submitting batch job...")
    batch_id = create_batch_job(client, batch_requests)

    # Wait for completion
    while not check_batch_status(client, batch_id):
        time.sleep(30)  # Check every 30 seconds

    # Process results
    logger.info("Processing batch results...")
    process_batch_results(client, batch_id, args.output)


if __name__ == "__main__":
    main()
