#!/usr/bin/env python3
"""
Combine comprehensive speaker profiles with their session participation data.
Creates a speaker-centric view optimized for prioritization.
"""

import pandas as pd
import sys


def combine_speaker_sessions():
    try:
        # Read the comprehensive speaker profiles with error reporting
        def bad_line_handler(line):
            print(f"BAD LINE: {line}")
            return None

        speakers_df = pd.read_csv(
            "data/groundswellag_sessions_speakers_final.csv",
            sep=";",
            on_bad_lines=bad_line_handler,
            engine="python",
        )
        print(f"Loaded {len(speakers_df)} speaker profiles")

        # Read the cleaned sessions data
        sessions_df = pd.read_csv("data/groundswellag_sessions_expanded_clean.csv")
        print(f"Loaded {len(sessions_df)} session records")

        # Group sessions by speaker while preserving field relationships
        def aggregate_sessions(group):
            # Create structured session records (tier|category|name|relevance_notes, etc.)
            sessions = []
            for _, row in group.iterrows():
                # Handle NaN values by converting to string
                tier = str(row["tier"]) if pd.notna(row["tier"]) else "N/A"
                category = str(row["category"]) if pd.notna(row["category"]) else "N/A"
                session_name = (
                    str(row["session_name"]) if pd.notna(row["session_name"]) else "N/A"
                )
                relevance_notes = (
                    str(row["relevance_notes"])
                    if pd.notna(row["relevance_notes"])
                    else "N/A"
                )

                session_record = f"{tier}|{category}|{session_name}|{relevance_notes}"
                sessions.append(session_record)

            return pd.Series(
                {
                    "session_records": "||".join(
                        sessions
                    ),  # Double pipe separates sessions
                    "session_names": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["session_name"].tolist()
                        ]
                    ),
                    "session_descriptions": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["description"].tolist()
                        ]
                    ),
                    "session_dates": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["date"].tolist()
                        ]
                    ),
                    "session_times": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["time"].tolist()
                        ]
                    ),
                    "session_locations": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["location"].tolist()
                        ]
                    ),
                    "session_tiers": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["tier"].tolist()
                        ]
                    ),
                    "session_categories": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["category"].tolist()
                        ]
                    ),
                    "session_relevance_notes": "|".join(
                        [
                            str(x) if pd.notna(x) else "N/A"
                            for x in group["relevance_notes"].tolist()
                        ]
                    ),
                }
            )

        session_groups = (
            sessions_df.groupby("speaker_name").apply(aggregate_sessions).reset_index()
        )

        print(f"Aggregated sessions for {len(session_groups)} unique speakers")

        # Merge speaker profiles with aggregated session data
        combined_df = pd.merge(
            speakers_df,
            session_groups,
            left_on="Name",
            right_on="speaker_name",
            how="left",
        )

        # Remove duplicate speaker_name column
        combined_df = combined_df.drop("speaker_name", axis=1)

        # Fill NaN values for speakers without sessions
        session_cols = [
            "session_records",
            "session_names",
            "session_descriptions",
            "session_dates",
            "session_times",
            "session_locations",
            "session_tiers",
            "session_categories",
            "session_relevance_notes",
        ]
        for col in session_cols:
            combined_df[col] = combined_df[col].fillna("No sessions found")

        # Reorder columns for prioritization workflow
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
            "session_tiers",
            "session_categories",
            "session_names",
            "session_relevance_notes",
            "session_records",
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
        existing_cols = [col for col in priority_columns if col in combined_df.columns]
        extra_cols = [col for col in combined_df.columns if col not in priority_columns]
        combined_df = combined_df[existing_cols + extra_cols]

        print(f"Combined dataset contains {len(combined_df)} speaker records")
        print(
            f"Speakers with sessions: {len(combined_df[combined_df['session_names'] != 'No sessions found'])}"
        )
        print(
            f"Speakers without sessions: {len(combined_df[combined_df['session_names'] == 'No sessions found'])}"
        )

        # Save the combined file
        combined_df.to_csv(
            "data/groundswellag_speakers_with_sessions_final.csv", sep=";", index=False
        )
        print(
            "Saved combined data to data/groundswellag_speakers_with_sessions_final.csv"
        )

        print(
            "\nFile optimized for speaker prioritization with session relationships preserved"
        )
        print(
            "session_records format: tier|category|name|relevance_notes (sessions separated by ||)"
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    combine_speaker_sessions()
