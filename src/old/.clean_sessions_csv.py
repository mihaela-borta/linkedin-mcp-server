#!/usr/bin/env python3
"""
Clean embedded newlines from the sessions CSV file.
"""

import pandas as pd
import sys
import csv


def clean_sessions_csv():
    try:
        # Try to read with different approaches
        print(
            "Attempting to read and clean data/groundswellag_sessions_expanded.csv..."
        )

        # First, let's try reading with error handling
        try:
            sessions_df = pd.read_csv(
                "data/groundswellag_sessions_expanded.csv", on_bad_lines="skip"
            )
            print(
                f"Successfully read {len(sessions_df)} records (some bad lines may have been skipped)"
            )
        except Exception as e:
            print(f"Standard read failed: {e}")
            # Try with Python engine and more permissive settings
            sessions_df = pd.read_csv(
                "data/groundswellag_sessions_expanded.csv",
                engine="python",
                on_bad_lines="skip",
                quoting=csv.QUOTE_MINIMAL,
            )
            print(f"Read {len(sessions_df)} records with Python engine")

        # Clean any embedded newlines from text fields
        text_columns = [
            "description",
            "speaker_bio",
            "relevance_notes",
            "session_name",
            "category",
        ]
        for col in text_columns:
            if col in sessions_df.columns:
                sessions_df[col] = (
                    sessions_df[col].astype(str).str.replace("\n", " ", regex=False)
                )
                sessions_df[col] = sessions_df[col].str.replace("\r", " ", regex=False)
                sessions_df[col] = sessions_df[col].str.replace(
                    "  ", " ", regex=False
                )  # Clean double spaces
                print(f"Cleaned newlines from {col}")

        # Save the cleaned file
        sessions_df.to_csv(
            "data/groundswellag_sessions_expanded_clean.csv",
            index=False,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
        )
        print(
            f"Saved cleaned data to data/groundswellag_sessions_expanded_clean.csv with {len(sessions_df)} records"
        )

        # Show the columns
        print("\nColumns in cleaned file:")
        for i, col in enumerate(sessions_df.columns):
            print(f"{i + 1:2d}. {col}")

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    clean_sessions_csv()
