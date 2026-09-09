"""
Combine handpicked and all session data for Groundswell speakers, aggregate sessions per speaker, and join with speaker bios using fuzzy matching.
"""

import pandas as pd
import os
import difflib
import argparse

# Main processing logic


def expand_sessions_by_speaker(df, session_cols):
    df = df.copy()
    df["speakers"] = df["speakers"].fillna("")
    df = df[df["speakers"] != ""]
    df["name"] = df["speakers"].str.split(" & ")
    df = df.explode("name")
    df["name"] = df["name"].str.strip()
    return df[session_cols + ["name"]]


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate and join session and speaker data for Groundswell."
    )
    parser.add_argument(
        "--all-sessions",
        type=str,
        default="data/groundswellag_sessions_clean.csv",
        help="CSV with all sessions (default: data/groundswellag_sessions_clean.csv)",
    )
    parser.add_argument(
        "--handpicked",
        type=str,
        default="data/groundswellag_sessions_handpicked.csv",
        help="CSV with handpicked sessions (default: data/groundswellag_sessions_handpicked.csv)",
    )
    parser.add_argument(
        "--speakers",
        type=str,
        default="data/groundswellag_speakers.csv",
        help="CSV with speaker bios (default: data/groundswellag_speakers.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/groundswellag_speakers_from_handpicked_sessions.csv",
        help="Output CSV file (default: data/groundswellag_speakers_from_handpicked_sessions.csv)",
    )
    args = parser.parse_args()

    all_sessions_path = args.all_sessions
    handpicked_path = args.handpicked
    speakers_path = args.speakers
    output_path = args.output

    # 1. Process handpicked sessions
    handpicked = pd.read_csv(handpicked_path)
    handpicked_expanded = expand_sessions_by_speaker(handpicked, ["session_name"])
    # Aggregate selected sessions per speaker
    speakers_selected_sessions = (
        handpicked_expanded.groupby("name")
        .agg({"session_name": lambda x: "|".join(x)})
        .reset_index()
    )
    speakers_selected_sessions["selected_sessions"] = speakers_selected_sessions[
        "session_name"
    ]
    speakers_selected_sessions["selected_sessions_count"] = (
        speakers_selected_sessions["session_name"].str.split("|").str.len()
    )
    speakers_selected_sessions = speakers_selected_sessions[
        ["name", "selected_sessions", "selected_sessions_count"]
    ]

    # 2. Process all sessions
    all_sessions = pd.read_csv(all_sessions_path)
    all_sessions_expanded = expand_sessions_by_speaker(
        all_sessions, ["session_name", "date", "time", "location", "description"]
    )
    # Aggregate all sessions per speaker
    agg_dict = {
        "session_name": lambda x: "|".join(x),
        "date": lambda x: "|".join(x),
        "time": lambda x: "|".join(x),
        "location": lambda x: "|".join(x),
        "description": lambda x: "|".join(x),
    }
    all_sessions_agg = all_sessions_expanded.groupby("name").agg(agg_dict).reset_index()
    all_sessions_agg["session_names"] = all_sessions_agg["session_name"]
    all_sessions_agg["session_dates"] = all_sessions_agg["date"]
    all_sessions_agg["session_times"] = all_sessions_agg["time"]
    all_sessions_agg["session_locations"] = all_sessions_agg["location"]
    all_sessions_agg["session_descriptions"] = all_sessions_agg["description"]
    all_sessions_agg["sessions_count"] = (
        all_sessions_agg["session_name"].str.split("|").str.len()
    )
    all_sessions_agg = all_sessions_agg[
        [
            "name",
            "session_names",
            "session_dates",
            "session_times",
            "session_locations",
            "session_descriptions",
            "sessions_count",
        ]
    ]

    # 3. Left join selected speakers with all sessions
    speakers_merged = pd.merge(
        speakers_selected_sessions, all_sessions_agg, on="name", how="left"
    )
    print(speakers_merged.shape)
    print(speakers_merged.head(1))

    # 4. Join with speakers bio (fuzzy match)
    speakers_df = pd.read_csv(speakers_path, usecols=["name", "bio"])
    print(speakers_df["name"].nunique())
    speakers_merged["speaker_alt_name"] = speakers_merged["name"].apply(
        lambda x: difflib.get_close_matches(x, speakers_df["name"], n=1, cutoff=0.7)[0]
        if difflib.get_close_matches(x, speakers_df["name"], n=1, cutoff=0.7)
        else x
    )
    speakers_final = pd.merge(
        speakers_merged,
        speakers_df,
        left_on="speaker_alt_name",
        right_on="name",
        how="left",
        suffixes=("", "_bio"),
    )

    # Reorder columns to put bio right after name
    column_order = [
        "name",
        "speaker_alt_name",
        "bio",
        "selected_sessions",
        "selected_sessions_count",
        "session_names",
        "session_dates",
        "session_times",
        "session_locations",
        "session_descriptions",
        "sessions_count",
    ]
    speakers_final = speakers_final[column_order]

    # 5. Output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    speakers_final.to_csv(output_path, index=False)
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
