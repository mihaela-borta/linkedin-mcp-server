#!/usr/bin/env python3
"""
Merge comprehensive speaker data from two CSV files.
Combines session aggregation data with detailed speaker profiles.
"""

import pandas as pd
import sys
import csv


def merge_comprehensive_speaker_data():
    try:
        # Read the session aggregation data (smaller dataset with session info)
        sessions_agg_df = pd.read_csv(
            "data/groundswellag_speakers_with_sessions_aggregated.csv", sep=";"
        )
        print(f"Loaded {len(sessions_agg_df)} records from sessions aggregation")

        # Read the comprehensive speaker profiles (larger dataset with detailed info)
        speakers_final_df = pd.read_csv(
            "data/groundswellag_sessions_speakers_final.csv",
            sep=";",
            on_bad_lines="skip",
            engine="python",
        )
        print(
            f"Loaded {len(speakers_final_df)} records from comprehensive speaker profiles"
        )

        # Merge on speaker_name (from sessions_agg) and Name (from speakers_final)
        merged_df = pd.merge(
            speakers_final_df,
            sessions_agg_df,
            left_on="Name",
            right_on="speaker_name",
            how="left",
        )

        print(f"Merged dataset contains {len(merged_df)} records")

        # Handle duplicate columns - keep the better version
        # Remove speaker_name (duplicate of Name)
        if "speaker_name" in merged_df.columns:
            merged_df = merged_df.drop("speaker_name", axis=1)

        # For speaker_bio and speaker_url, keep the version from speakers_final (more comprehensive)
        # Remove duplicates from sessions aggregation if they exist
        columns_to_check = ["speaker_bio", "speaker_url"]
        for col in columns_to_check:
            # If there are duplicate columns with suffixes, keep the one without suffix
            if f"{col}_x" in merged_df.columns and f"{col}_y" in merged_df.columns:
                # Keep the _x version (from speakers_final) and rename it
                merged_df[col] = merged_df[f"{col}_x"]
                merged_df = merged_df.drop([f"{col}_x", f"{col}_y"], axis=1)
                print(f"Resolved duplicate {col} columns")

        # Reorder columns for optimal workflow
        priority_columns = [
            "Name",
            "Full_Name",
            "Company",
            "Title",
            "LinkedIn",
            "Location",
            "Industry",
            "Brief_Profile",
            "Detailed_Profile",
            "session_count",
            "session_names",
            "session_descriptions",
            "session_dates",
            "session_times",
            "session_locations",
            "Media_Links",
            "Professional_Links",
            "speaker_bio",
            "speaker_url",
        ]

        # Reorder columns (keep any extra columns at the end)
        existing_cols = [col for col in priority_columns if col in merged_df.columns]
        extra_cols = [col for col in merged_df.columns if col not in priority_columns]
        merged_df = merged_df[existing_cols + extra_cols]

        # Fill NaN values for speakers without sessions
        session_cols = [
            "session_count",
            "session_names",
            "session_descriptions",
            "session_dates",
            "session_times",
            "session_locations",
        ]
        for col in session_cols:
            if col in merged_df.columns:
                if col == "session_count":
                    merged_df[col] = merged_df[col].fillna(0)
                else:
                    merged_df[col] = merged_df[col].fillna("No sessions found")

        # Save the merged file
        merged_df.to_csv(
            "data/groundswellag_comprehensive_speakers_final.csv",
            sep=";",
            index=False,
            quoting=csv.QUOTE_ALL,
        )
        print(
            "Saved comprehensive data to data/groundswellag_comprehensive_speakers_final.csv"
        )

        # Show summary statistics
        speakers_with_sessions = len(merged_df[merged_df["session_count"] > 0])
        speakers_without_sessions = len(merged_df[merged_df["session_count"] == 0])

        print("\nSummary:")
        print(f"Total speakers: {len(merged_df)}")
        print(f"Speakers with sessions: {speakers_with_sessions}")
        print(f"Speakers without sessions: {speakers_without_sessions}")

        if speakers_with_sessions > 0:
            total_sessions = merged_df[merged_df["session_count"] > 0][
                "session_count"
            ].sum()
            avg_sessions = merged_df[merged_df["session_count"] > 0][
                "session_count"
            ].mean()
            max_sessions = merged_df["session_count"].max()

            print(f"Total session participations: {total_sessions}")
            print(f"Average sessions per active speaker: {avg_sessions:.1f}")
            print(f"Maximum sessions for one speaker: {int(max_sessions)}")

            # Show top speakers by session count
            top_speakers = merged_df.nlargest(5, "session_count")[
                ["Name", "Company", "session_count"]
            ]
            print("\nTop 5 speakers by session participation:")
            for _, row in top_speakers.iterrows():
                if row["session_count"] > 0:
                    company = row["Company"] if pd.notna(row["Company"]) else "N/A"
                    print(
                        f"  {row['Name']} ({company}): {int(row['session_count'])} sessions"
                    )

        print(
            "\nComprehensive dataset ready with detailed speaker profiles and session data"
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    merge_comprehensive_speaker_data()
