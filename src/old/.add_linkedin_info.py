#!/usr/bin/env python3
"""
Add LinkedIn matching info to the final scored speakers dataset.
Merges Name, match_found, and linkedin_slug from merged_linkedin_data.csv.
"""

import pandas as pd
import sys
import csv


def add_linkedin_info():
    try:
        # Read the LinkedIn data (source of linkedin info)
        linkedin_df = pd.read_csv("data/merged_linkedin_data.csv")
        print(f"Loaded {len(linkedin_df)} records from LinkedIn data")

        # Select only the columns we need
        linkedin_subset = linkedin_df[["Name", "match_found", "linkedin_slug"]].copy()
        print(f"Selected LinkedIn info for {len(linkedin_subset)} speakers")

        # Read the comprehensive scored speakers data
        speakers_df = pd.read_csv(
            "data/groundswellag_speakers_final_all_sessions_scored.csv",
            sep=";",
            quoting=csv.QUOTE_ALL,
            engine="python",
        )
        print(f"Loaded {len(speakers_df)} records from scored speakers data")

        # Merge on Name column
        merged_df = pd.merge(speakers_df, linkedin_subset, on="Name", how="left")

        print(f"Merged dataset contains {len(merged_df)} records")

        # Check merge results
        linkedin_matches = len(merged_df[merged_df["match_found"].notna()])
        linkedin_found = len(merged_df[merged_df["match_found"] == True])
        linkedin_slugs = len(
            merged_df[
                merged_df["linkedin_slug"].notna() & (merged_df["linkedin_slug"] != "")
            ]
        )

        print("LinkedIn matching results:")
        print(f"  Speakers with LinkedIn search results: {linkedin_matches}")
        print(f"  Speakers with LinkedIn profiles found: {linkedin_found}")
        print(f"  Speakers with LinkedIn slugs: {linkedin_slugs}")

        # Fill NaN values for speakers without LinkedIn data
        merged_df["match_found"] = merged_df["match_found"].fillna(False)
        merged_df["linkedin_slug"] = merged_df["linkedin_slug"].fillna("")

        # Reorder columns - put LinkedIn info near other contact info
        # Find the position of LinkedIn column to insert nearby
        cols = list(merged_df.columns)
        linkedin_pos = cols.index("LinkedIn") if "LinkedIn" in cols else len(cols)

        # Remove LinkedIn columns from their current positions
        cols_no_linkedin = [
            col for col in cols if col not in ["match_found", "linkedin_slug"]
        ]

        # Insert LinkedIn columns after the LinkedIn URL column
        final_cols = (
            cols_no_linkedin[: linkedin_pos + 1]
            + ["match_found", "linkedin_slug"]
            + cols_no_linkedin[linkedin_pos + 1 :]
        )

        merged_df = merged_df[final_cols]

        # Save the updated file
        merged_df.to_csv(
            "data/groundswellag_speakers_final_all_sessions_scored.csv",
            sep=";",
            index=False,
            quoting=csv.QUOTE_ALL,
        )
        print(
            "Saved updated data with LinkedIn info to data/groundswellag_speakers_final_all_sessions_scored.csv"
        )

        # Show summary of top scored speakers with LinkedIn info
        if "priority_score" in merged_df.columns:
            top_scored = merged_df.nlargest(5, "priority_score")[
                ["Name", "priority_score", "match_found", "linkedin_slug", "Company"]
            ]
            print("\nTop 5 scored speakers with LinkedIn status:")
            for _, row in top_scored.iterrows():
                linkedin_status = "✓ Found" if row["match_found"] else "✗ Not found"
                slug = f" ({row['linkedin_slug']})" if row["linkedin_slug"] else ""
                company = row["Company"] if pd.notna(row["Company"]) else "N/A"
                print(
                    f"  {row['Name']} ({company}) - Score: {row['priority_score']:.1f} - LinkedIn: {linkedin_status}{slug}"
                )

        print("\nDataset now includes LinkedIn matching results for strategic outreach")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_linkedin_info()
