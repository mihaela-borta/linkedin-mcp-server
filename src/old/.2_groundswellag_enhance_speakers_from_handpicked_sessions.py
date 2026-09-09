#!/usr/bin/env python3
"""
Expand shortlisted sessions with speaker details and bios.
"""

import pandas as pd
import sys
from pathlib import Path


def expand_shortlist_speakers():
    """Expand shortlisted sessions with speaker details."""

    # File paths
    shortlist_file = "data/groundswellag_sessions_handpicked.csv"
    speakers_file = "data/groundswellag_speakers.csv"
    output_file = "data/groundswellag_speakers_from_handpicked_sessions_1.csv"

    # Read all files
    try:
        shortlist_df = pd.read_csv(shortlist_file)
        print(f"Loaded {len(shortlist_df)} shortlisted sessions")

        speakers_df = pd.read_csv(
            speakers_file, quotechar='"', escapechar="\\", on_bad_lines="warn"
        )
        print(f"Loaded {len(speakers_df)} speakers")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    # Split speakers column and explode to one speaker per row
    print("Exploding speakers to individual rows...")
    shortlist_df["speakers"] = shortlist_df["speakers"].str.split(" & ")
    exploded_df = shortlist_df.explode("speakers").reset_index(drop=True)

    # Remove rows with empty speakers
    exploded_df = exploded_df.dropna(subset=["speakers"])
    exploded_df = exploded_df[exploded_df["speakers"].str.strip() != ""]

    # Clean speaker names (strip whitespace)
    exploded_df["speakers"] = exploded_df["speakers"].str.strip()
    exploded_df.rename(columns={"speakers": "name"}, inplace=True)

    # Add speaker bios
    print("Adding speaker bios...")
    exploded_df = exploded_df.merge(
        speakers_df[["name", "bio", "url"]], left_on="name", right_on="name", how="left"
    )

    exploded_df = exploded_df.rename(
        columns={"name": "speaker_name", "bio": "speaker_bio", "url": "speaker_url"}
    )

    # Aggregate by 'speaker_name', 'speaker_bio', 'speaker_url' the session_name, date, time, location. The resulting fields should be | separated and contain only strings (the brackets should be removed).
    exploded_df = (
        exploded_df.groupby(["speaker_name", "speaker_bio", "speaker_url"])
        .agg(
            {
                "session_name": lambda x: "|".join(x),
                "date": lambda x: "|".join(x),
                "time": lambda x: "|".join(x),
                "location": lambda x: "|".join(x),
            }
        )
        .reset_index()
    )

    # Rename aggregated columns and add sessions count
    exploded_df = exploded_df.rename(
        columns={
            "session_name": "session_names",
            "date": "session_dates",
            "time": "session_times",
            "location": "session_locations",
        }
    )
    exploded_df["session_count"] = exploded_df["session_names"].str.count("\|") + 1

    # Reorder columns for better readability
    columns = [
        "speaker_name",
        "speaker_bio",
        "speaker_url",
        "session_names",
        "session_dates",
        "session_times",
        "session_locations",
        "session_count",
    ]
    exploded_df = exploded_df[columns]

    # Save results
    exploded_df.to_csv(output_file, index=False)
    print(f"Expanded data saved to: {output_file}")

    # Show top speakers by session count
    print("\nTop speakers by session count:")
    top_speakers = exploded_df.nlargest(5, "session_count")[
        ["speaker_name", "session_count"]
    ]
    for _, row in top_speakers.iterrows():
        print(f"  {row['speaker_name']}: {row['session_count']} sessions")

    return exploded_df


if __name__ == "__main__":
    # Check if input files exist
    required_files = [
        "data/groundswellag_sessions_handpicked.csv",
        "data/groundswellag_speakers.csv",
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"Error: {file_path} not found")
            sys.exit(1)

    expand_shortlist_speakers()
