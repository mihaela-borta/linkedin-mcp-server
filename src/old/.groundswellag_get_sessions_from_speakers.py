#!/usr/bin/env python3
"""
Extract unique session information from Groundswell speakers CSV.
Extracts columns: session_title_1, session_date_1, session_time_1,
session_location_1, session_description_1, session_url_1
"""

import pandas as pd
import sys
from pathlib import Path


def extract_sessions(input_file: str, output_file: str = None):
    """Extract unique session info from speakers CSV."""

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

    # Select and rename columns
    session_columns = [
        "session_title_1",
        "session_date_1",
        "session_time_1",
        "session_location_1",
        "session_description_1",
        "session_url_1",
    ]

    # Check if columns exist
    missing_cols = [col for col in session_columns if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns: {missing_cols}")
        sys.exit(1)

    # Extract session data
    sessions_df = df[session_columns].copy()

    # Remove _1 suffix from column names
    sessions_df.columns = [col.replace("_1", "") for col in sessions_df.columns]

    # Remove rows where session_title is empty/null
    sessions_df = sessions_df.dropna(subset=["session_title"])
    sessions_df = sessions_df[sessions_df["session_title"].str.strip() != ""]

    # Remove exact duplicates
    initial_count = len(sessions_df)
    sessions_df = sessions_df.drop_duplicates()
    final_count = len(sessions_df)

    print(
        f"Found {initial_count} sessions, {final_count} unique sessions after deduplication"
    )

    # Set output file
    if output_file is None:
        output_file = "data/sessions.csv"

    # Save to CSV
    sessions_df.to_csv(output_file, index=False)
    print(f"Sessions saved to: {output_file}")

    # Print summary
    print("\nSessions by date:")
    if "session_date" in sessions_df.columns:
        date_counts = sessions_df["session_date"].value_counts().sort_index()
        for date, count in date_counts.items():
            print(f"  {date}: {count} sessions")

    return sessions_df


if __name__ == "__main__":
    input_file = "data/groundwellag_speakers.csv"

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    extract_sessions(input_file)
