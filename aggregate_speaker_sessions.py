#!/usr/bin/env python3
"""
Aggregate sessions for speakers from groundswellag_sessions_clean.csv.
Matches speakers by name and aggregates their session participation.
"""

import pandas as pd
import sys


def aggregate_speaker_sessions():
    try:
        # Read the speaker list
        speakers_df = pd.read_csv("data/groundswellag_sessions_speakers.csv")
        print(f"Loaded {len(speakers_df)} speakers from speaker list")

        # Read the sessions data
        sessions_df = pd.read_csv("data/groundswellag_sessions_clean.csv")
        print(f"Loaded {len(sessions_df)} sessions from sessions data")

        # Create aggregated results for each speaker
        results = []

        for _, speaker_row in speakers_df.iterrows():
            speaker_name = speaker_row["speaker_name"]

            # Find sessions where this speaker participates
            # The speakers column uses & to separate multiple speakers
            matching_sessions = sessions_df[
                sessions_df["speakers"].str.contains(
                    speaker_name, case=False, na=False, regex=False
                )
            ]

            # Aggregate session information
            if len(matching_sessions) > 0:
                session_count = len(matching_sessions)
                session_names = "|".join(
                    matching_sessions["session_name"].astype(str).tolist()
                )
                session_descriptions = "|".join(
                    matching_sessions["description"].astype(str).tolist()
                )
                session_dates = "|".join(matching_sessions["date"].astype(str).tolist())
                session_times = "|".join(matching_sessions["time"].astype(str).tolist())
                session_locations = "|".join(
                    matching_sessions["location"].astype(str).tolist()
                )
            else:
                session_count = 0
                session_names = "No sessions found"
                session_descriptions = "No sessions found"
                session_dates = "No sessions found"
                session_times = "No sessions found"
                session_locations = "No sessions found"

            # Create result row with original speaker data plus session aggregation
            result_row = speaker_row.to_dict()
            result_row.update(
                {
                    "session_count": session_count,
                    "session_names": session_names,
                    "session_descriptions": session_descriptions,
                    "session_dates": session_dates,
                    "session_times": session_times,
                    "session_locations": session_locations,
                }
            )

            results.append(result_row)

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        # Reorder columns to put session data at the end
        original_cols = [col for col in speakers_df.columns]
        session_cols = [
            "session_count",
            "session_names",
            "session_descriptions",
            "session_dates",
            "session_times",
            "session_locations",
        ]

        results_df = results_df[original_cols + session_cols]

        # Save the results
        results_df.to_csv(
            "data/groundswellag_speakers_with_sessions_aggregated.csv",
            sep=";",
            index=False,
        )
        print(
            "Saved aggregated data to data/groundswellag_speakers_with_sessions_aggregated.csv"
        )

        # Show summary statistics
        speakers_with_sessions = len(results_df[results_df["session_count"] > 0])
        speakers_without_sessions = len(results_df[results_df["session_count"] == 0])
        total_session_participations = results_df["session_count"].sum()

        print("\nSummary:")
        print(f"Total speakers: {len(results_df)}")
        print(f"Speakers with sessions: {speakers_with_sessions}")
        print(f"Speakers without sessions: {speakers_without_sessions}")
        print(f"Total session participations: {total_session_participations}")

        if speakers_with_sessions > 0:
            avg_sessions = results_df[results_df["session_count"] > 0][
                "session_count"
            ].mean()
            max_sessions = results_df["session_count"].max()
            print(f"Average sessions per active speaker: {avg_sessions:.1f}")
            print(f"Maximum sessions for one speaker: {max_sessions}")

            # Show speakers with most sessions
            top_speakers = results_df.nlargest(5, "session_count")[
                ["speaker_name", "session_count"]
            ]
            print("\nTop 5 speakers by session count:")
            for _, row in top_speakers.iterrows():
                if row["session_count"] > 0:
                    print(f"  {row['speaker_name']}: {row['session_count']} sessions")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    aggregate_speaker_sessions()
