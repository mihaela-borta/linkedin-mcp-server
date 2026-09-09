#!/usr/bin/env python3
"""
Merge profile search terms data by filling missing information from the second file
where only name is filled in the first file.
"""

import pandas as pd
import sys


def main():
    # Read both CSV files
    try:
        df1 = pd.read_csv("data/profile_search_terms_groundswell.csv", sep=";")
        df2 = pd.read_csv("data/profile_search_terms_groundswell_2.csv", sep=";")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"File 1 has {len(df1)} rows")
    print(f"File 2 has {len(df2)} rows")

    # Find entries in df1 that only have name filled (organization, job_title, search_keywords are empty/null)
    name_only_mask = (
        (df1["name"].notna())
        & (df1["name"] != "")
        & ((df1["organization"].isna()) | (df1["organization"] == ""))
        & ((df1["job_title"].isna()) | (df1["job_title"] == ""))
        & ((df1["search_keywords"].isna()) | (df1["search_keywords"] == ""))
    )

    name_only_entries = df1[name_only_mask]
    print(f"Found {len(name_only_entries)} entries with only name filled in first file")

    if len(name_only_entries) > 0:
        print("\nSample name-only entries:")
        for _, row in name_only_entries.head(3).iterrows():
            print(f"- {row['name']}")

    # Start with df1 as base
    result_df = df1.copy()

    # For each name-only entry in df1, look for complete data in df2
    updates_count = 0
    for idx, row in name_only_entries.iterrows():
        name = row["name"]

        # Find matching entry in df2
        matching_entries = df2[df2["name"] == name]

        if len(matching_entries) > 0:
            # Use the first match
            match = matching_entries.iloc[0]

            # Update the row in result_df with data from df2
            result_df.at[idx, "organization"] = (
                match["organization"] if pd.notna(match["organization"]) else ""
            )
            result_df.at[idx, "job_title"] = (
                match["job_title"] if pd.notna(match["job_title"]) else ""
            )
            result_df.at[idx, "search_keywords"] = (
                match["search_keywords"] if pd.notna(match["search_keywords"]) else ""
            )

            updates_count += 1
            print(f"Updated data for: {name}")

    print(f"\nSuccessfully updated {updates_count} entries with data from second file")

    # Save the result
    result_df.to_csv(
        "data/profile_search_terms_groundswell_3.csv", sep=";", index=False
    )
    print("Saved merged data to data/profile_search_terms_groundswell_3.csv")

    # Show summary of final file
    final_complete_entries = result_df[
        (result_df["name"].notna())
        & (result_df["name"] != "")
        & (result_df["organization"].notna())
        & (result_df["organization"] != "")
        & (result_df["job_title"].notna())
        & (result_df["job_title"] != "")
        & (result_df["search_keywords"].notna())
        & (result_df["search_keywords"] != "")
    ]

    print("\nFinal file statistics:")
    print(f"- Total entries: {len(result_df)}")
    print(f"- Complete entries (all fields filled): {len(final_complete_entries)}")
    print(f"- Entries with only name: {len(result_df) - len(final_complete_entries)}")


if __name__ == "__main__":
    main()
