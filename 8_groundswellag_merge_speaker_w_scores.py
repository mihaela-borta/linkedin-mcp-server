#!/usr/bin/env python3
"""
Merge speaker scoring data with comprehensive speaker profiles.
Combines prioritization scores with detailed speaker information.
"""

import pandas as pd
import sys
import csv
import argparse


def merge_scored_speakers(scores_path, speakers_path, output_path):
    try:
        # Read the scoring data
        scores_df = pd.read_csv(scores_path, sep=";")
        print(f"Loaded {len(scores_df)} scoring records")

        # Read the comprehensive speaker data
        speakers_df = pd.read_csv(
            speakers_path,
            sep=";",
            quoting=csv.QUOTE_ALL,
            engine="python",
            on_bad_lines="skip",
        )
        print(f"Loaded {len(speakers_df)} speaker records")

        # Merge on name column
        merged_df = pd.merge(speakers_df, scores_df, on="name", how="left")

        print(f"Merged dataset contains {len(merged_df)} records")
        print(
            f"Records with scores: {len(merged_df[merged_df['priority_score'].notna()])}"
        )
        print(
            f"Records without scores: {len(merged_df[merged_df['priority_score'].isna()])}"
        )

        # Reorder columns for prioritization workflow - put scoring data first
        priority_columns = [
            "name",
            "speaker_alt_name",
            "priority_score",
            "customer_category",
            "network_level",
            "approach_type",
            "outreach_timing",
            "key_value_proposition",
            "critical_notes",
            "full_name",
            "company",
            "title",
            "linkedin",
            "location",
            "industry",
            "brief_profile",
            "detailed_profile",
            "session_names",
            "session_relevance_notes",
            "session_count",
            "session_descriptions",
            "session_dates",
            "session_times",
            "session_locations",
            "media_links",
            "professional_links",
            "bio",
            "speaker_url",
        ]

        # Reorder columns (keep any extra columns at the end)
        existing_cols = [col for col in priority_columns if col in merged_df.columns]
        extra_cols = [col for col in merged_df.columns if col not in priority_columns]
        merged_df = merged_df[existing_cols + extra_cols]

        # Save the merged file
        merged_df.to_csv(output_path, sep=";", index=False, quoting=csv.QUOTE_ALL)
        print(f"Saved merged data to {output_path}")

        # Show summary statistics
        if "priority_score" in merged_df.columns:
            scored_speakers = merged_df[merged_df["priority_score"].notna()]
            if len(scored_speakers) > 0:
                print("\nScoring summary:")
                print(
                    f"Average priority score: {scored_speakers['priority_score'].mean():.2f}"
                )
                print(
                    f"Score range: {scored_speakers['priority_score'].min():.1f} - {scored_speakers['priority_score'].max():.1f}"
                )

                # Show top 5 scored speakers
                top_speakers = scored_speakers.nlargest(5, "priority_score")[
                    ["name", "priority_score", "company", "customer_category"]
                ]
                print("\nTop 5 prioritized speakers:")
                for idx, row in top_speakers.iterrows():
                    print(
                        f"  {row['name']} ({row['company']}) - Score: {row['priority_score']:.1f} - {row['customer_category']}"
                    )

        print(
            f"\nFinal dataset ready for prioritized outreach with {len(merged_df)} speaker records"
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge speaker scoring data with comprehensive speaker profiles."
    )
    parser.add_argument(
        "--scores",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_scored.csv",
        help="CSV file with speaker scores (default: data/groundswellag_speakers_from_handpicked_scored.csv)",
    )
    parser.add_argument(
        "--speakers",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_w_background.csv",
        help="CSV file with comprehensive speaker profiles (default: data/groundswellag_speakers_from_handpicked_w_background.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_w_scores_1.csv",
        help="Output CSV file (default: data/groundswellag_speakers_from_handpicked_w_scores_1.csv)",
    )
    args = parser.parse_args()
    merge_scored_speakers(args.scores, args.speakers, args.output)
