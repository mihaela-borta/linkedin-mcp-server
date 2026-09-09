#!/usr/bin/env python3
"""
Extract unique speakers and their bios from expanded sessions data.
Removes duplicates and creates a clean list of speakers with their information.
"""

import pandas as pd
import sys
from pathlib import Path


def extract_unique_speakers(input_file: str, output_file: str = None):
    """Extract unique speakers from expanded sessions data."""

    # Read the expanded sessions file
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} session-speaker combinations")
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Check required columns
    required_columns = ["speaker_name", "speaker_bio", "speaker_url"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        sys.exit(1)

    # Extract unique speakers with their information
    print("Extracting unique speakers...")

    # Remove rows where speaker_name is empty/null
    df_clean = df.dropna(subset=["speaker_name"])
    df_clean = df_clean[df_clean["speaker_name"].str.strip() != ""]

    # Get unique speakers (drop duplicates based on speaker_name)
    # Keep first occurrence in case of slight variations in bio/url
    unique_speakers = df_clean.drop_duplicates(subset=["speaker_name"], keep="first")

    # Select only speaker-related columns
    speakers_df = unique_speakers[["speaker_name", "speaker_bio", "speaker_url"]].copy()

    # Sort by speaker name for easier reading
    speakers_df = speakers_df.sort_values("speaker_name")

    # Reset index
    speakers_df = speakers_df.reset_index(drop=True)

    # Set output file
    if output_file is None:
        output_file = "data/groundswellag_sessions_speakers_2.csv"

    # Save to CSV
    speakers_df.to_csv(output_file, index=False)
    print(f"Unique speakers saved to: {output_file}")

    # Print summary
    print("\nSummary:")
    print(f"Total unique speakers: {len(speakers_df)}")
    print(f"Speakers with bios: {speakers_df['speaker_bio'].notna().sum()}")
    print(f"Speakers with URLs: {speakers_df['speaker_url'].notna().sum()}")

    # Show speakers without bios (if any)
    missing_bios = speakers_df[
        speakers_df["speaker_bio"].isna() | (speakers_df["speaker_bio"] == "")
    ]
    if len(missing_bios) > 0:
        print(f"\nSpeakers without bios ({len(missing_bios)}):")
        for speaker in missing_bios["speaker_name"].head(10):  # Show first 10
            print(f"  - {speaker}")
        if len(missing_bios) > 10:
            print(f"  ... and {len(missing_bios) - 10} more")

    # Show sample of speakers with bios
    print("\nSample speakers with bios:")
    speakers_with_bios = speakers_df[
        speakers_df["speaker_bio"].notna() & (speakers_df["speaker_bio"] != "")
    ]
    for i, row in speakers_with_bios.head(5).iterrows():
        bio_preview = (
            str(row["speaker_bio"])[:80] + "..."
            if len(str(row["speaker_bio"])) > 80
            else str(row["speaker_bio"])
        )
        print(f"  - {row['speaker_name']}: {bio_preview}")

    return speakers_df


if __name__ == "__main__":
    input_file = "data/groundswellag_sessions_expanded_2.csv"

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    extract_unique_speakers(input_file)
