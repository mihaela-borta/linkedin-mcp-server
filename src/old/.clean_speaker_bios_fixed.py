#!/usr/bin/env python3
"""
Clean speaker bio column in Groundswell speakers CSV.
Keeps text up to the first ** or \[…\] encountered.
"""

import pandas as pd
import sys
from pathlib import Path


def clean_bio(bio_text):
    """Clean bio text by keeping only content up to first ** or \[…\]."""
    if pd.isna(bio_text) or bio_text == "":
        return bio_text

    bio_str = str(bio_text)

    # Find position of first ** or \[…\]
    double_star_pos = bio_str.find("**")
    ellipsis_pos = bio_str.find("\\[…\\]")

    # Find the earliest position that's not -1
    positions = [pos for pos in [double_star_pos, ellipsis_pos] if pos != -1]

    if positions:
        # Keep text up to the first marker
        first_marker_pos = min(positions)
        cleaned_bio = bio_str[:first_marker_pos].strip()
        return cleaned_bio
    else:
        # No markers found, return original
        return bio_str.strip()


def clean_speaker_bios(input_file: str, output_file: str = None):
    """Clean speaker bios in the CSV file."""

    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} speaker records")
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Check if bio column exists
    if "bio" not in df.columns:
        print("Error: 'bio' column not found in CSV")
        sys.exit(1)

    # Save original for comparison
    original_bios = df["bio"].copy()

    # Clean the bio column
    print("Cleaning bio column...")
    df["bio"] = df["bio"].apply(clean_bio)

    # Count changes
    changed_count = sum(df["bio"] != original_bios)
    print(f"Cleaned {changed_count} speaker bios")

    # Set output file
    if output_file is None:
        output_file = input_file  # Overwrite original

    # Save cleaned data
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to: {output_file}")

    # Show some examples
    print("\nExample cleaned bios:")
    for i, (original, cleaned) in enumerate(
        zip(original_bios.head(3), df["bio"].head(3))
    ):
        if str(original) != str(cleaned):
            print(f"\nSpeaker {i + 1}:")
            print(f"Original: {str(original)[:150]}...")
            print(f"Cleaned:  {str(cleaned)[:150]}...")

    return df


if __name__ == "__main__":
    input_file = "data/groundswellag_speakers.csv"

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    clean_speaker_bios(input_file)
