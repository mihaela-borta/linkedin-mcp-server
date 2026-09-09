#!/usr/bin/env python3
"""
Extract speaker information from event schedule CSV/TSV files.

This script parses event schedule files to extract speaker names, job titles,
and organizations, handling cases where speakers may have multiple roles.
"""

import argparse
import logging
import re
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def parse_speaker_info(text) -> Dict[str, str]:
    # Split by " (" to separate name from roles
    parts = text.split(' (', 1)
    name = parts[0].strip()
    roles = parts[1].rstrip(')') if len(parts) > 1 else ''

    # Process roles
    role_parts = roles.split(' & ') if roles else []
    result = [name, None, None, None, None]
   
    for i, part in enumerate(role_parts[:2]):
        part = part.strip()  # Remove leading/trailing whitespace
        if part.startswith('- '):
            # Handle "- Organization" format
            result[i*2+2] = part[2:].strip() or None
        elif ' - ' in part:
            # Handle "Job - Organization" format
            job, org = part.split(' - ', 1)
            result[i*2+1] = job.strip() or None
            result[i*2+2] = org.strip() or None
        else:
            # Just organization
            result[i*2+2] = part or None
    
    return dict(zip(['name', 'job_title', 'organization', 'job_title2', 'organization2'], result))

def extract_speakers_from_sessions(
    input_file: Path,
    separator: str = ";",
    output_file: Path = None
) -> pd.DataFrame:
    """
    Extract speaker information from event sessions file.
    
    Args:
        input_file: Path to input CSV/TSV file
        separator: File separator (default: ";")
        output_file: Path to output file (optional)
    
    Returns:
        DataFrame with speaker information
    """
    try:
        df = pd.read_csv(input_file, sep=separator, engine='python')
        logging.info(f"Successfully read {len(df)} rows from {input_file}")
    except Exception as e:
        logging.error(f"Error reading file {input_file}: {e}")
        raise
    
    all_speakers = []
    
    for idx, row in df.iterrows():
        session_date = row.get("session_date", "")
        session_time = row.get("session_time", "")
        session_name = row.get("session_name", "")
        topic = row.get("topic", "")
        
        speakers_text = row.get("speakers", "")
        if pd.notna(speakers_text) and speakers_text.strip():
            individual_speakers = [s.strip() for s in speakers_text.split("|")]
            
            for speaker in individual_speakers:
                if speaker.strip():
                    info = parse_speaker_info(speaker)
                    if info['name']:
                        #if info['name'] == 
                        all_speakers.append({
                            "session_date": session_date,
                            "session_time": session_time,
                            "session_name": session_name,
                            "topic": topic,
                            "speaker_name": info['name'],
                            "job_title": info['job_title'],
                            "organization": info['organization'],
                            "job_title2": info['job_title2'],
                            "organization2": info['organization2'],
                            "source": "speakers"
                        })
        
        moderator_text = row.get("moderator", "")
        if pd.notna(moderator_text) and moderator_text.strip():
            info = parse_speaker_info(moderator_text)
            if info['name']:  # Only add if we have a name
                all_speakers.append({
                    "session_date": session_date,
                    "session_time": session_time,
                    "session_name": session_name,
                    "topic": topic,
                    "speaker_name": info['name'],
                    "job_title": info['job_title'],
                    "organization": info['organization'],
                    "job_title2": info['job_title2'],
                    "organization2": info['organization2'],
                    "source": "moderator"
                })
    
    speakers_df = pd.DataFrame(all_speakers)
    
    if speakers_df.empty:
        logging.warning("No speakers found in the file")
        return speakers_df
    
    speakers_df = speakers_df.dropna(subset=["speaker_name"])
    speakers_df = speakers_df[speakers_df["speaker_name"].str.strip() != ""]
    
    speakers_df = speakers_df.drop_duplicates(
        subset=["speaker_name", "session_name", "source"],
        keep="first"
    )
    
    logging.info(f"Extracted {len(speakers_df)} speaker entries")
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        speakers_df.to_csv(output_file, index=False, sep=";")
        logging.info(f"Saved speaker data to {output_file}")
    
    return speakers_df


def main():
    """Main function to run the speaker extraction script."""
    parser = argparse.ArgumentParser(
        description="Extract speaker information from event schedule files"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input CSV/TSV file path"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/os2025/os2025_speakers.csv"),
        help="Output CSV file path (default: data/os2025/os2025_speakers.csv)"
    )
    parser.add_argument(
        "-s", "--separator",
        default=";",
        help="File separator (default: ';')"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if not args.input_file.exists():
        logging.error(f"Input file not found: {args.input_file}")
        return 1
    
    try:
        speakers_df = extract_speakers_from_sessions(
            input_file=args.input_file,
            separator=args.separator,
            output_file=args.output
        )
        
        if not speakers_df.empty:
            logging.info("Speaker extraction completed successfully!")
            logging.info(f"Total speakers extracted: {len(speakers_df)}")
            
            print("\nSample of extracted speakers:")
            print(speakers_df[["speaker_name", "job_title", "organization", "session_name"]].head(10))
        else:
            logging.warning("No speakers were extracted")
            return 1
            
    except Exception as e:
        logging.error(f"Error during speaker extraction: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
