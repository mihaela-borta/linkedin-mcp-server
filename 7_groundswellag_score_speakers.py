#!/usr/bin/env python3
"""
Score and prioritize Groundswell Festival speakers for Muryo outreach using Claude API.
This version uses all session data for each speaker and removes geographic relevance from scoring and output.
"""

import os
import logging
import argparse
from anthropic import Anthropic
from typing import Dict, List
import pandas as pd
from utils import clean_string
from utils import (
    jsonl_to_csv,
    create_batch_job,
    poll_for_batch_completion,
    download_results_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("groundswell_scorer_comprehensive")


def load_input_data(filename: str) -> List[Dict]:
    """Load the CSV data with speaker information"""
    speakers = []
    try:
        df = pd.read_csv(filename, sep=";")
        logger.info(f"Loaded {len(df)} speaker records from {filename}")
        for _, row in df.iterrows():
            # Lowercase all keys for consistency
            speaker = {
                col.lower(): row[col] if pd.notna(row[col]) else ""
                for col in df.columns
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
            "text": """You are evaluating potential speakers at Groundswell Festival for Muryo, an AI copilot that de-risks the transition to sustainable crop production by bridging the science/implementation gap—turning research into actionable, farm-specific guidance that balances economic viability with environmental stewardship.

## Business Focus
- **Primary customers**: Agronomist consultants (crop production focus)
- **Secondary customers**: Progressive farmers (especially those growing crops sustainably)
- **Adjacent markets**: Seed companies, crop protection companies, fertilizer companies, agricultural lenders, crop insurers, grain traders/elevators, food processors, mills, bakeries, breweries, retailers (procurement/sustainability), water management companies, precision ag companies, supply chain/traceability companies, commodity trading firms
- **Mission**: De-risk sustainable transitions through science-backed, farm-specific guidance

## Scoring Framework (1-10 scale)

### Customer Fit (60% weight)
- **9-10**: Primary - Crop consultants/agronomists at consultancies, independent advisors
- **8-9**: Secondary - Progressive crop farmers implementing sustainable practices
- **7-8**: Strategic high-value - Food company sustainability teams, ag tech companies with advisory focus
- **6-7**: Adjacent high-value - Seed companies, crop protection companies, fertilizer companies, agricultural lenders, crop insurers, grain traders/elevators, food processors, mills, bakeries, breweries, retailers (procurement/sustainability), water management companies, precision ag companies, supply chain/traceability companies, commodity trading firms
- **5-6**: Research/Policy - Research institutions, policy makers, soil health specialists, certification bodies
- **3-4**: Relevant - Equipment manufacturers, environmental consultants, packaging companies, logistics/transport
- **1-2**: Low relevance - Livestock only, non-agricultural, unrelated sectors

### Network/Expertise Relevance (40% weight)
- **9-10**: Senior executives at major consultancies/organizations, keynote speakers, published experts
- **7-8**: Department heads, association leaders, recognized thought leaders, multiple session speakers
- **5-6**: Mid-level professionals, active in networks, single session speakers
- **3-4**: Junior roles but well-connected, emerging voices in sustainable agriculture
- **1-2**: Limited influence, narrow networks, minimal speaking presence

## Key Assessment Criteria
1. **Crop focus over livestock** - Higher scores for crop production specialists
2. **Value chain position** - Upstream (seeds, inputs) and downstream (processing, retail) players who depend on crop quality/sustainability
3. **Risk assessment experience** - Agricultural lenders/insurers score highly for adjacent market validation
4. **Supply chain influence** - Food processors, retailers, traders who can drive sustainable sourcing requirements
5. **Science-to-practice translation** - Consultants bridging research gap = highest relevance
6. **Sustainable agriculture expertise** - Direct alignment with business mission
7. **Network influence** - Speaking, writing, association leadership
8. **Senior decision-making roles** - Can influence organizational or even national/international level adoption or sourcing decisions

## CRITICAL: Output Format for CSV Columns
You MUST return ONLY a JSON object with these EXACT field names that will become CSV columns:

{
    "name": Name as provided,
    "priority_score": X.X,
    "customer_category": "Primary_Customer|Secondary_Customer|Strategic_High_Value|Adjacent_High_Value|Research_Policy|Low_Relevance",
    "network_level": "High|Medium|Low",
    "key_value_proposition": "One sentence explaining why relevant for Muryo's de-risking value prop",
    "outreach_timing": "Before_Event|During_Event|Post_Event",
    "approach_type": "Validation_Interview|Partnership_Discussion|Advisory_Role|Strategic_Networking|Strategic_Celebrity",
    "critical_notes": "Key sessions, special relevance, or standout details (max 50 characters)"
}

These field names will be used directly as CSV column headers. Do not modify, add, or remove any field names.

## Outreach Timing Logic:
- **High scores (8-10)** = Before_Event
- **Medium scores (5-7)** = During_Event
- **Low scores (1-4)** = Post_Event

## Special Case: World-Renowned Voices
For speakers with massive platforms (major podcasts, celebrity status, 100K+ followers):
- **Only pursue if**: Direct strategic value (decision-maker at target customer), perfect content alignment (sustainable crop production focus), advisory potential, or media opportunity reaching your exact audience
- **Skip if**: Generic agriculture content, pure brand building, no decision-making power, or audience mismatch
- **Timing**: Always Before_Event for strategic preparation, but expect low response rates
- **Approach**: Focus time on tier 2 voices instead for better ROI unless clear strategic fit

Mark these speakers with approach_type: "Strategic_Celebrity" and add "HIGH_BARRIER" to critical_notes.


speaker information and ALL session data for the speaker will be provided in the user message. You must consider ALL sessions the speaker is involved in for your assessment, not just a subset.
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    for i, speaker in enumerate(speakers):
        # Build speaker description with all session info
        speaker_info = f"""name: {speaker.get("name", "")}
company: {speaker.get("company", "")}
title: {speaker.get("title", "")}
location: {speaker.get("location", "")}
industry: {speaker.get("industry", "")}
speaker bio from festival webpage: {speaker.get("speaker_bio", "")}
brief profile: {speaker.get("brief_profile", "")}
detailed profile: {speaker.get("detailed_profile", "")}

selected sessions: {speaker.get("selected_sessions", "")}
all sessions: {speaker.get("session_names", "")}
all sessions descriptions: {speaker.get("session_descriptions", "")}
media links: {speaker.get("media_links", "")}
professional links: {speaker.get("professional_links", "")}
"""

        user_prompt = f"""Please score this speaker for outreach priority at Groundswell Festival:

{speaker_info}

Analyze this speaker based on:
1. Customer fit for Muryo's AI copilot (crop consultants = highest, progressive farmers = high, adjacent markets = medium)
2. Network influence and expertise level
3. Sustainable agriculture alignment
4. Decision-making capability

Consider speaker influence level: World-renowned voices (major podcasts, celebrity status) should only be prioritized if there's direct strategic value beyond networking. Factor low response probability into your assessment.

IMPORTANT: You must consider both the sessions we found most relevant, as well as all sessions the speaker is involved in for your assessment. Do NOT consider geographic relevance in your scoring. Return ONLY a JSON object with the exact field names specified in the system prompt. These field names will become CSV columns in the output file. Do not include any additional text, explanations, or formatting outside the JSON object."""

        # Use imported clean_string for custom_id
        name = clean_string(speaker.get("name", ""))[:30]
        org = clean_string(speaker.get("company", ""))[:30]
        custom_id = f"{name}_{org}"

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
        description="Score and prioritize Groundswell Festival speakers for Muryo outreach using Claude (comprehensive version)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_w_background.csv",
        help="Input CSV file with speaker data (default: data/groundswellag_speakers_from_handpicked_w_background.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_scored_1.csv",
        help="Output CSV file for scored results (default: data/groundswellag_speakers_from_handpicked_scored.csv)",
    )
    parser.add_argument(
        "--jsonl",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_scored_1.jsonl",
        help="Intermediate JSONL file to store batch results (default: data/groundswellag_speakers_from_handpicked_scored.jsonl)",
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
    logger.info("Loading input data...")
    speakers = load_input_data(args.input)
    logger.info(f"Loaded {len(speakers)} speakers")
    logger.info("Creating batch requests...")
    batch_requests = create_batch_requests(speakers)
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
