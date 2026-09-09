#!/usr/bin/env python3
"""
Extract speakers from shortlisted Groundswell sessions.
Matches speakers with their sessions based on session titles and organizes by session.
"""

import pandas as pd
import sys
from pathlib import Path


def extract_shortlisted_speakers(
    shortlist_file: str, speakers_file: str, output_file: str = None
):
    """Extract speakers participating in shortlisted sessions."""

    # Read the shortlisted sessions
    try:
        shortlist_df = pd.read_csv(shortlist_file)
        print(f"Loaded {len(shortlist_df)} shortlisted sessions")
    except FileNotFoundError:
        print(f"Error: {shortlist_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading shortlist CSV: {e}")
        sys.exit(1)

    # Read the full speakers list
    try:
        speakers_df = pd.read_csv(speakers_file)
        print(f"Loaded {len(speakers_df)} speaker records")
    except FileNotFoundError:
        print(f"Error: {speakers_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading speakers CSV: {e}")
        sys.exit(1)

    # Get shortlisted session titles
    shortlisted_sessions = set(shortlist_df["Session Title"].str.strip())
    print(f"Shortlisted sessions: {len(shortlisted_sessions)}")

    # Extract speakers for shortlisted sessions
    results = []

    for _, speaker in speakers_df.iterrows():
        speaker_name = speaker["name"]
        speaker_bio = speaker.get("bio", "")
        speaker_url = speaker.get("url", "")

        # Check all session columns (1, 2, 3)
        for session_num in [1, 2, 3]:
            session_title_col = f"session_title_{session_num}"
            session_date_col = f"session_date_{session_num}"
            session_time_col = f"session_time_{session_num}"
            session_location_col = f"session_location_{session_num}"
            session_url_col = f"session_url_{session_num}"

            if session_title_col in speaker.index and pd.notna(
                speaker[session_title_col]
            ):
                session_title = str(speaker[session_title_col]).strip()

                if session_title in shortlisted_sessions:
                    # Get additional session info
                    session_date = speaker.get(session_date_col, "")
                    session_time = speaker.get(session_time_col, "")
                    session_location = speaker.get(session_location_col, "")
                    session_url = speaker.get(session_url_col, "")

                    # Get shortlist info for this session
                    shortlist_info = shortlist_df[
                        shortlist_df["Session Title"].str.strip() == session_title
                    ]
                    if not shortlist_info.empty:
                        rank = shortlist_info.iloc[0].get("Rank", "")
                        priority = shortlist_info.iloc[0].get("Priority/Type", "")
                        score = shortlist_info.iloc[0].get("Score", "")
                        strategic_value = shortlist_info.iloc[0].get(
                            "Strategic Value", ""
                        )
                        key_stakeholders = shortlist_info.iloc[0].get(
                            "Key Stakeholders", ""
                        )
                    else:
                        rank = priority = score = strategic_value = key_stakeholders = (
                            ""
                        )

                    results.append(
                        {
                            "session_title": session_title,
                            "session_date": session_date,
                            "session_time": session_time,
                            "session_location": session_location,
                            "session_url": session_url,
                            "rank": rank,
                            "priority_type": priority,
                            "score": score,
                            "strategic_value": strategic_value,
                            "key_stakeholders": key_stakeholders,
                            "speaker_name": speaker_name,
                            "speaker_bio": speaker_bio,
                            "speaker_url": speaker_url,
                        }
                    )

    if not results:
        print("No speakers found for shortlisted sessions")
        return pd.DataFrame()

    # Create DataFrame and sort by session title, then speaker name
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(["session_title", "speaker_name"])

    print(f"Found {len(results_df)} speaker-session matches")
    print(f"Unique speakers: {results_df['speaker_name'].nunique()}")
    print(f"Sessions represented: {results_df['session_title'].nunique()}")

    # Set output file
    if output_file is None:
        output_file = "data/groundswellag_shortlisted_speakers.csv"

    # Save to CSV
    results_df.to_csv(output_file, index=False)
    print(f"Shortlisted speakers saved to: {output_file}")

    # Print summary by session
    print("\nSpeakers by session:")
    session_counts = (
        results_df.groupby("session_title")["speaker_name"]
        .count()
        .sort_values(ascending=False)
    )
    for session, count in session_counts.items():
        print(f"  {session}: {count} speakers")

    return results_df


if __name__ == "__main__":
    shortlist_file = "data/groundswellag_sessions_2.csv"
    speakers_file = "data/groundswellag_speakers.csv"

    # Check if input files exist
    if not Path(shortlist_file).exists():
        print(f"Error: {shortlist_file} not found")
        sys.exit(1)

    if not Path(speakers_file).exists():
        print(f"Error: {speakers_file} not found")
        sys.exit(1)

    extract_shortlisted_speakers(shortlist_file, speakers_file)
