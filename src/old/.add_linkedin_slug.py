#!/usr/bin/env python3
"""
Add LinkedIn slug column to merged_linkedin_data.csv.
Extracts the last part of the LinkedIn URL as the slug.
"""

import pandas as pd
import sys


def add_linkedin_slug():
    try:
        # Read the merged LinkedIn data
        df = pd.read_csv("data/merged_linkedin_data.csv")
        print(f"Loaded {len(df)} records from merged_linkedin_data.csv")

        # Extract LinkedIn slug from linkedin_url column
        def extract_linkedin_slug(url):
            if pd.isna(url) or url == "":
                return ""

            # Remove trailing slash if present
            url = str(url).rstrip("/")

            # Split by '/' and get the last part
            parts = url.split("/")
            if len(parts) > 0:
                return parts[-1]
            else:
                return ""

        # Apply the function to create the new column
        df["linkedin_slug"] = df["linkedin_url"].apply(extract_linkedin_slug)

        # Show some examples
        print("\nSample LinkedIn slug extractions:")
        sample_data = df[["linkedin_url", "linkedin_slug"]].head(5)
        for _, row in sample_data.iterrows():
            print(f"  {row['linkedin_url']} -> {row['linkedin_slug']}")

        # Count non-empty slugs
        non_empty_slugs = len(df[df["linkedin_slug"] != ""])
        print(f"\nExtracted {non_empty_slugs} LinkedIn slugs from {len(df)} records")

        # Save the updated file
        df.to_csv("data/merged_linkedin_data.csv", index=False)
        print(
            "Saved updated data with linkedin_slug column to data/merged_linkedin_data.csv"
        )

        # Show column list
        print(f"\nUpdated columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure data/merged_linkedin_data.csv exists")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_linkedin_slug()
