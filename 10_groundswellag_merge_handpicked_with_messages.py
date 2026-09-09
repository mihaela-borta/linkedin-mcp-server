import pandas as pd
import sys
import argparse


def merge_handpicked_with_messages(speakers_path, messages_path, output_path):
    """
    Merge groundswellag_speakers_from_handpicked_sessions.csv with groundswellag_speakers_with_messages.csv
    Left merge on lowercase 'name' column
    """
    # Read the CSV files
    try:
        speakers_df = pd.read_csv(sessions_path, sep=";")
        speakers_df.columns = [col.lower() for col in speakers_df.columns]
        print(speakers_df.columns)
        messages_df = pd.read_csv(messages_path, sep=";")
        messages_df.columns = [col.lower() for col in messages_df.columns]
        print(f"Loaded {len(speakers_df)} handpicked speaker records")
        print(f"Loaded {len(messages_df)} message records")
        print(messages_df.columns)
        print(speakers_df.columns)
    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    merged_df = pd.merge(speakers_df, messages_df, on="name", how="left")
    final_columns = [
        "name",
        "bio",
        "message",
        "selected_sessions",
        "priority_score",
        "key_value_proposition",
        "critical_notes",
        "title",
        "linkedin",
        "match_found",
        "brief_profile",
        "detailed_profile",
        "media_links",
        "professional_links",
        "character_count",
        "confidence_level",
        "personalization_source",
        "send_recommendation",
        "customer_category",
        "network_level",
        "approach_type",
        "outreach_timing",
        "linkedin_slug",
        "location",
        "industry",
        "full_name",
        "company",
        "speaker_url",
        "selected_sessions_count",
        "session_names",
        "session_dates",
        "session_times",
        "session_locations",
        "session_descriptions",
        "sessions_count",
    ]
    available_columns = [col for col in final_columns if col in merged_df.columns]
    merged_df = merged_df[available_columns]
    print(f"Final merged dataframe contains {len(merged_df)} records")
    print(f"Available columns: {available_columns}")
    merged_df.to_csv(output_path, sep=";", index=False)
    print(f"Saved merged data to {output_path}")
    print("\nSample merged records:")
    print(merged_df[["name", "message"]].head(5))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge handpicked session speakers with generated messages."
    )
    parser.add_argument(
        "--speakers",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_w_scores_1.csv",
        help="CSV file with handpicked session speakers (default: data/groundswellag_speakers_from_handpicked_sessions.csv)",
    )
    parser.add_argument(
        "--messages",
        type=str,
        default="data/groundswellag_outreach_messages_1.csv",
        help="CSV file with generated messages (default: data/groundswellag_speakers_with_messages.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_with_messages_from_handpicked_sessions_1.csv",
        help="Output CSV file (default: data/groundswellag_speakers_with_messages_from_handpicked_sessions_1.csv)",
    )
    args = parser.parse_args()
    merge_handpicked_with_messages(args.sessions, args.messages, args.output)
