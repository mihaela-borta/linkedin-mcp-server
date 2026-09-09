import pandas as pd
import sys


def merge_speaker_data():
    """
    Merge groundswellag_comprehensive_speakers_final.csv with groundswellag_outreach_messages.csv
    First sorts the outreach messages by Name column alphabetically, then merges by Name column
    """

    # Read the CSV files
    try:
        speakers_df = pd.read_csv(
            "data/groundswellag_speakers_final_all_sessions_scored.csv", sep=";"
        )
        messages_df = pd.read_csv("data/groundswellag_outreach_messages.csv", sep=";")

        print(f"Loaded {len(speakers_df)} speaker records")
        print(f"Loaded {len(messages_df)} message records")

    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    # Sort the messages dataframe by Name column alphabetically
    messages_df = messages_df.sort_values("Name")
    print("Sorted messages by Name column")

    # Save the sorted messages file
    messages_df.to_csv(
        "data/groundswellag_outreach_messages_sorted.csv", sep=";", index=False
    )
    print("Saved sorted messages to data/groundswellag_outreach_messages_sorted.csv")

    # Merge the dataframes on the Name column
    merged_df = pd.merge(speakers_df, messages_df, on="Name", how="left")

    print(f"Merged result contains {len(merged_df)} records")
    print(f"Records with messages: {len(merged_df[merged_df['message'].notna()])}")
    print(f"Records without messages: {len(merged_df[merged_df['message'].isna()])}")

    # Save the merged result
    output_file = "data/groundswellag_speakers_with_messages.csv"
    merged_df.to_csv(output_file, sep=";", index=False)
    print(f"Saved merged data to {output_file}")

    # Display some sample merged records
    print("\nSample merged records:")
    print(merged_df[["Name", "Company", "Title", "message"]].head(10))


if __name__ == "__main__":
    merge_speaker_data()
