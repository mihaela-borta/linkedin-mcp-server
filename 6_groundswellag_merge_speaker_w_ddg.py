#!/usr/bin/env python3
"""
Merge groundswell speaker data from two CSV files.
Combines parsed DDG results with sessions speakers data using a left join on name.
"""

import pandas as pd
import sys
import csv
import argparse


def merge_groundswell_data(ddg_path, sessions_path, output_path):
    try:
        # Read the two CSV files
        ddg_df = pd.read_csv(ddg_path, sep=";")
        sessions_df = pd.read_csv(sessions_path)

        print(f"Loaded {len(ddg_df)} records from {ddg_path}")
        print(f"Loaded {len(sessions_df)} records from {sessions_path}")

        # Lowercase all columns for consistency
        ddg_df.columns = [c.lower() for c in ddg_df.columns]
        sessions_df.columns = [c.lower() for c in sessions_df.columns]

        # Merge on 'name'
        merged_df = pd.merge(
            sessions_df, ddg_df, on="name", how="left", suffixes=("", "_ddg")
        )

        # Clean any embedded newlines from text fields
        text_columns = ["brief_profile", "detailed_profile", "speaker_bio"]
        for col in text_columns:
            if col in merged_df.columns:
                merged_df[col] = (
                    merged_df[col].astype(str).str.replace("\n", " ", regex=False)
                )
                merged_df[col] = merged_df[col].str.replace("\r", " ", regex=False)

        print(f"Merged dataset contains {len(merged_df)} records (joined on name)")

        # Save to output file with proper CSV quoting to handle line breaks
        merged_df.to_csv(
            output_path,
            sep=";",
            index=False,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
            doublequote=True,
        )
        print(f"Saved merged data to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge parsed DDG results with session speakers data using a left join on name."
    )
    parser.add_argument(
        "--ddg",
        type=str,
        default="data/groundswellag_speakers_parsed_ddg_results.csv",
        help="CSV file with parsed DDG results (default: data/groundswellag_speakers_parsed_ddg_results.csv)",
    )
    parser.add_argument(
        "--sessions",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_sessions.csv",
        help="CSV file with session speakers data (default: data/groundswellag_speakers_from_handpicked_sessions.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_w_background.csv",
        help="Output CSV file (default: data/groundswellag_speakers_from_handpicked_w_background.csv)",
    )
    args = parser.parse_args()
    merge_groundswell_data(args.ddg, args.sessions, args.output)
